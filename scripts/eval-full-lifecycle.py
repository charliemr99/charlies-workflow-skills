#!/usr/bin/env python3
"""Run a real multi-turn Charlie's Workflow lifecycle in Codex or Claude Code."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = ROOT / "evals" / "charlies-workflow-full-lifecycle.json"
FIXTURE_PATH = ROOT / "evals" / "fixtures" / "feedback-inbox"
ORACLE_PATH = ROOT / "evals" / "oracles" / "feedback-inbox.mjs"
EVIDENCE_BOUNDARY = "real-harness-lifecycle-evaluation"
DECANT_VERSION = "0.4.0"
CLAUDE_SKILL_SYSTEM_PROMPT = (
    "The user explicitly invoked the project-scoped charlies-workflow skill. "
    "Before any task action, load charlies-workflow with the Skill tool and "
    "follow it for the entire session."
)
INVOCATIONS = {
    "codex": "$charlies-workflow",
    "claude": "/charlies-workflow",
}
IGNORED_EVAL_PREFIXES = (
    ".agents/",
    ".claude/",
    "node_modules/",
    "output/",
    "playwright-report/",
    "test-results/",
)


class EvaluationError(RuntimeError):
    """A failed precondition or lifecycle assertion."""


def load_scenario(path: Path = SCENARIO_PATH) -> dict[str, Any]:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    if scenario.get("schema_version") != 1:
        raise EvaluationError("Unsupported full lifecycle scenario schema")
    if scenario.get("evidence_boundary") != EVIDENCE_BOUNDARY:
        raise EvaluationError(
            f"Scenario evidence_boundary must be {EVIDENCE_BOUNDARY}"
        )
    turns = scenario.get("turns")
    if not isinstance(turns, list) or len(turns) != 4:
        raise EvaluationError("Full lifecycle scenario must contain four turns")
    required_turn_keys = {
        "id",
        "expected_phase",
        "forbid_source_changes",
        "prompt",
    }
    for turn in turns:
        if not isinstance(turn, dict) or not required_turn_keys.issubset(turn):
            raise EvaluationError("Full lifecycle turn has an invalid shape")
    return scenario


def render_prompt(harness: str, prompt: str) -> str:
    return prompt.replace("{{workflow}}", INVOCATIONS[harness])


def _codex_execution_flags() -> list[str]:
    return [
        "--json",
        "--color",
        "never",
        "--approve-for-me",
        "-c",
        "sandbox_workspace_write.network_access=true",
    ]


def _codex_resume_flags() -> list[str]:
    return [
        "--skip-git-repo-check",
        "--json",
        "-c",
        "sandbox_workspace_write.network_access=true",
    ]


def _claude_execution_flags() -> list[str]:
    return [
        "--output-format",
        "stream-json",
        "--verbose",
        "--append-system-prompt",
        CLAUDE_SKILL_SYSTEM_PROMPT,
        "--permission-mode",
        "dontAsk",
        "--allowedTools",
        "Bash,Read,Edit,Write,Glob,Grep,Skill",
    ]


def build_initial_command(
    harness: str,
    workspace: Path,
    prompt: str,
    session_id: str | None,
    additional_writable: Path | None = None,
) -> list[str]:
    prompt = render_prompt(harness, prompt)
    if harness == "codex":
        if session_id is not None:
            raise EvaluationError("Codex assigns its session id after startup")
        command = [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "-C",
            str(workspace),
            *_codex_execution_flags(),
        ]
        if additional_writable is not None:
            command.extend(["--add-dir", str(additional_writable)])
        return [*command, prompt]
    if harness == "claude":
        if session_id is None:
            raise EvaluationError("Claude requires a fixed session id")
        return [
            "claude",
            "-p",
            *_claude_execution_flags(),
            "--session-id",
            session_id,
            prompt,
        ]
    raise EvaluationError(f"Unsupported harness: {harness}")


def build_resume_command(
    harness: str,
    workspace: Path,
    session_id: str,
    prompt: str,
    additional_writable: Path | None = None,
) -> list[str]:
    if harness == "codex":
        del workspace, additional_writable
        return [
            "codex",
            "exec",
            "resume",
            *_codex_resume_flags(),
            session_id,
            prompt,
        ]
    if harness == "claude":
        del workspace
        return [
            "claude",
            "-p",
            *_claude_execution_flags(),
            "--resume",
            session_id,
            prompt,
        ]
    raise EvaluationError(f"Unsupported harness: {harness}")


def extract_codex_session_id(transcript: str) -> str:
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started" and isinstance(
            event.get("thread_id"), str
        ):
            return event["thread_id"]
        if event.get("type") == "thread.started" and isinstance(
            event.get("threadId"), str
        ):
            return event["threadId"]
    raise EvaluationError("Codex did not emit a thread.started session id")


def find_session_log(harness: str, session_id: str, home: Path) -> Path:
    if harness == "codex":
        root = home / ".codex" / "sessions"
        pattern = f"*{session_id}*.jsonl"
    elif harness == "claude":
        root = home / ".claude" / "projects"
        pattern = f"{session_id}.jsonl"
    else:
        raise EvaluationError(f"Unsupported harness: {harness}")
    matches = sorted(
        root.rglob(pattern) if root.is_dir() else [],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise EvaluationError(
            f"Unable to locate {harness} session log for {session_id} under {root}"
        )
    return matches[0]


def _read_json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _parse_json_lines(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _timestamp_ms(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round(parsed.timestamp() * 1000)


def _sum_fields(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[str, int]:
    return {
        field: sum(
            int(row.get(field, 0))
            for row in rows
            if isinstance(row.get(field, 0), (int, float))
        )
        for field in fields
    }


def parse_codex_native_telemetry(
    session_log: Path, turn_names: list[str]
) -> dict[str, Any]:
    """Read authoritative per-turn Codex usage before Decant normalization."""
    records = _read_json_lines(session_log)
    session_meta: dict[str, Any] = {}
    turn_order: list[str] = []
    turns: dict[str, dict[str, Any]] = {}
    current_turn_id: str | None = None
    context_window_tokens = 0
    peak_context_tokens = 0
    tool_totals: dict[str, int] = {}

    for record in records:
        record_type = record.get("type")
        payload = record.get("payload")
        if record_type == "session_meta" and isinstance(payload, dict):
            session_meta = payload
            continue
        if record_type == "turn_context" and isinstance(payload, dict):
            turn_id = payload.get("turn_id")
            if isinstance(turn_id, str):
                turn = turns.setdefault(turn_id, {"harness_turn_id": turn_id})
                turn["model"] = payload.get("model")
                turn["reasoning_effort"] = payload.get("effort")
            continue
        if record_type == "response_item" and isinstance(payload, dict):
            if payload.get("type") != "custom_tool_call":
                continue
            metadata = payload.get("internal_chat_message_metadata_passthrough")
            turn_id = metadata.get("turn_id") if isinstance(metadata, dict) else None
            if not isinstance(turn_id, str):
                turn_id = current_turn_id
            tool_input = payload.get("input")
            matches = (
                re.findall(r"tools\.([A-Za-z0-9_]+)\s*\(", tool_input)
                if isinstance(tool_input, str)
                else []
            )
            tool_name = matches[0] if matches else str(payload.get("name", "unknown"))
            tool_totals[tool_name] = tool_totals.get(tool_name, 0) + 1
            if isinstance(turn_id, str):
                turn = turns.setdefault(turn_id, {"harness_turn_id": turn_id})
                per_turn = turn.setdefault("tools", {})
                per_turn[tool_name] = per_turn.get(tool_name, 0) + 1
            continue
        if record_type != "event_msg" or not isinstance(payload, dict):
            continue
        event_type = payload.get("type")
        if event_type == "task_started":
            turn_id = payload.get("turn_id")
            if not isinstance(turn_id, str):
                continue
            current_turn_id = turn_id
            if turn_id not in turn_order:
                turn_order.append(turn_id)
            turn = turns.setdefault(turn_id, {"harness_turn_id": turn_id})
            turn["started_at"] = record.get("timestamp")
        elif event_type == "token_count" and isinstance(payload.get("info"), dict):
            info = payload["info"]
            context_window_tokens = max(
                context_window_tokens, int(info.get("model_context_window") or 0)
            )
            last_usage = info.get("last_token_usage")
            if isinstance(last_usage, dict):
                peak_context_tokens = max(
                    peak_context_tokens, int(last_usage.get("input_tokens") or 0)
                )
            if current_turn_id is not None:
                usage = info.get("total_token_usage")
                if isinstance(usage, dict):
                    turns.setdefault(
                        current_turn_id, {"harness_turn_id": current_turn_id}
                    )["usage"] = dict(usage)
        elif event_type == "task_complete":
            turn_id = payload.get("turn_id")
            if not isinstance(turn_id, str):
                continue
            turn = turns.setdefault(turn_id, {"harness_turn_id": turn_id})
            turn["ended_at"] = record.get("timestamp")
            turn["duration_ms"] = int(payload.get("duration_ms") or 0)
            turn["time_to_first_token_ms"] = int(
                payload.get("time_to_first_token_ms") or 0
            )
            current_turn_id = None

    rendered_turns: list[dict[str, Any]] = []
    for index, turn_id in enumerate(turn_order):
        turn = turns[turn_id]
        usage = turn.get("usage") if isinstance(turn.get("usage"), dict) else {}
        cached = int(usage.get("cached_input_tokens") or 0)
        input_tokens = int(usage.get("input_tokens") or 0)
        rendered_turns.append(
            {
                "id": turn_names[index] if index < len(turn_names) else f"turn-{index + 1}",
                "harness_turn_id": turn_id,
                "started_at": turn.get("started_at"),
                "ended_at": turn.get("ended_at"),
                "duration_ms": int(turn.get("duration_ms") or 0),
                "time_to_first_token_ms": int(
                    turn.get("time_to_first_token_ms") or 0
                ),
                "usage": {
                    "input_tokens": input_tokens,
                    "cached_input_tokens": cached,
                    "uncached_input_tokens": input_tokens - cached,
                    "cache_write_input_tokens": int(
                        usage.get("cache_write_input_tokens") or 0
                    ),
                    "output_tokens": int(usage.get("output_tokens") or 0),
                    "reasoning_output_tokens": int(
                        usage.get("reasoning_output_tokens") or 0
                    ),
                    "total_tokens": int(usage.get("total_tokens") or 0),
                },
                "tool_calls": sum(turn.get("tools", {}).values()),
                "tools": dict(sorted(turn.get("tools", {}).items())),
            }
        )

    usage_rows = [turn["usage"] for turn in rendered_turns]
    token_totals = _sum_fields(
        usage_rows,
        (
            "input_tokens",
            "cached_input_tokens",
            "uncached_input_tokens",
            "cache_write_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
            "total_tokens",
        ),
    )
    starts = [_timestamp_ms(turn.get("started_at")) for turn in rendered_turns]
    ends = [_timestamp_ms(turn.get("ended_at")) for turn in rendered_turns]
    valid_starts = [value for value in starts if value is not None]
    valid_ends = [value for value in ends if value is not None]
    wall_time_ms = (
        max(valid_ends) - min(valid_starts)
        if valid_starts and valid_ends
        else sum(turn["duration_ms"] for turn in rendered_turns)
    )
    turn_active_ms = sum(turn["duration_ms"] for turn in rendered_turns)
    model: str | None = None
    reasoning_effort: str | None = None
    for turn_id in turn_order:
        turn = turns[turn_id]
        if model is None and isinstance(turn.get("model"), str):
            model = turn["model"]
        if reasoning_effort is None and isinstance(
            turn.get("reasoning_effort"), str
        ):
            reasoning_effort = turn["reasoning_effort"]
    return {
        "source": "codex-native-log",
        "model": model,
        "reasoning_effort": reasoning_effort,
        "harness_version": session_meta.get("cli_version"),
        "model_provider": session_meta.get("model_provider"),
        "session": {
            "started_at": rendered_turns[0].get("started_at") if rendered_turns else None,
            "ended_at": rendered_turns[-1].get("ended_at") if rendered_turns else None,
            "wall_time_ms": wall_time_ms,
            "turn_active_ms": turn_active_ms,
            "inter_turn_gap_ms": max(0, wall_time_ms - turn_active_ms),
            "context_window_tokens": context_window_tokens,
            "peak_context_tokens": peak_context_tokens,
        },
        "tokens": token_totals,
        "turns": rendered_turns,
        "tools": {
            "total_calls": sum(tool_totals.values()),
            "by_name": dict(sorted(tool_totals.items())),
            "errors": 0,
        },
        "model_usage": {},
        "native_cost_usd": None,
    }


def parse_claude_native_telemetry(
    session_log: Path, turn_transcripts: list[dict[str, str]]
) -> dict[str, Any]:
    """Preserve Claude Code's cache, cost, model, and per-turn result fields."""
    session_records = _read_json_lines(session_log)
    timestamps = [
        timestamp
        for record in session_records
        if (timestamp := _timestamp_ms(record.get("timestamp"))) is not None
    ]
    rendered_turns: list[dict[str, Any]] = []
    tool_totals: dict[str, int] = {}
    model_usage: dict[str, dict[str, Any]] = {}
    model: str | None = None
    harness_version: str | None = None
    tool_errors = 0

    for source_turn in turn_transcripts:
        records = _parse_json_lines(source_turn["transcript"])
        result: dict[str, Any] = {}
        per_turn_tools: dict[str, int] = {}
        for record in records:
            if record.get("type") == "system" and record.get("subtype") == "init":
                if model is None and isinstance(record.get("model"), str):
                    model = record["model"]
                if harness_version is None and isinstance(
                    record.get("claude_code_version"), str
                ):
                    harness_version = record["claude_code_version"]
            if record.get("type") == "assistant":
                message = record.get("message")
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        name = str(block.get("name", "unknown"))
                        per_turn_tools[name] = per_turn_tools.get(name, 0) + 1
                        tool_totals[name] = tool_totals.get(name, 0) + 1
            if record.get("type") == "user":
                message = record.get("message")
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, list):
                    tool_errors += sum(
                        1
                        for block in content
                        if isinstance(block, dict)
                        and block.get("type") == "tool_result"
                        and block.get("is_error") is True
                    )
            if record.get("type") == "result":
                result = record

        usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
        result_models = (
            result.get("modelUsage")
            if isinstance(result.get("modelUsage"), dict)
            else {}
        )
        for name, values in result_models.items():
            if not isinstance(values, dict):
                continue
            aggregate = model_usage.setdefault(name, {})
            for field, value in values.items():
                if not isinstance(value, (int, float)):
                    continue
                if field in {"contextWindow", "maxOutputTokens"}:
                    aggregate[field] = max(aggregate.get(field, 0), value)
                else:
                    aggregate[field] = aggregate.get(field, 0) + value
        rendered_turns.append(
            {
                "id": source_turn["id"],
                "duration_ms": int(result.get("duration_ms") or 0),
                "api_duration_ms": int(result.get("duration_api_ms") or 0),
                "model_turns": int(result.get("num_turns") or 0),
                "usage": {
                    "input_tokens": int(usage.get("input_tokens") or 0),
                    "cache_creation_input_tokens": int(
                        usage.get("cache_creation_input_tokens") or 0
                    ),
                    "cache_read_input_tokens": int(
                        usage.get("cache_read_input_tokens") or 0
                    ),
                    "output_tokens": int(usage.get("output_tokens") or 0),
                },
                "tool_calls": sum(per_turn_tools.values()),
                "tools": dict(sorted(per_turn_tools.items())),
                "native_cost_usd": float(result.get("total_cost_usd") or 0),
            }
        )

    usage_rows = [turn["usage"] for turn in rendered_turns]
    token_totals = _sum_fields(
        usage_rows,
        (
            "input_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "output_tokens",
        ),
    )
    wall_time_ms = (
        max(timestamps) - min(timestamps)
        if timestamps
        else sum(turn["duration_ms"] for turn in rendered_turns)
    )
    turn_active_ms = sum(turn["duration_ms"] for turn in rendered_turns)
    return {
        "source": "claude-native-log-and-results",
        "model": model,
        "reasoning_effort": None,
        "harness_version": harness_version,
        "model_provider": "anthropic",
        "session": {
            "started_at": None,
            "ended_at": None,
            "wall_time_ms": wall_time_ms,
            "turn_active_ms": turn_active_ms,
            "api_time_ms": sum(turn["api_duration_ms"] for turn in rendered_turns),
            "inter_turn_gap_ms": max(0, wall_time_ms - turn_active_ms),
            "model_turns": sum(turn["model_turns"] for turn in rendered_turns),
        },
        "tokens": token_totals,
        "turns": rendered_turns,
        "tools": {
            "total_calls": sum(tool_totals.values()),
            "by_name": dict(sorted(tool_totals.items())),
            "errors": tool_errors,
        },
        "model_usage": model_usage,
        "native_cost_usd": sum(
            turn["native_cost_usd"] for turn in rendered_turns
        ),
    }


def build_decant_plan(session_log: Path, evidence_dir: Path) -> dict[str, list[str]]:
    database = evidence_dir / "decant.db"
    exports = evidence_dir / "exports"
    base = [
        "npx",
        "--yes",
        f"@dosu/decant@{DECANT_VERSION}",
        "--db",
        str(database),
    ]
    read = [*base, "--json", "--no-sync"]
    return {
        "sync": [*base, "--json", "sync", "--path", str(session_log)],
        "sessions": [*read, "ls", "--limit", "10"],
        "stats": [*read, "stats", "--by", "model"],
        "economics": [*read, "economics"],
        "files": [*read, "files", "--group", "path", "--limit", "100"],
        "tools": [*read, "tool", "stats", "--limit", "100"],
        "mcp": [*read, "mcp", "stats", "--limit", "100"],
        "trajectory": [
            *base,
            "--no-sync",
            "export",
            "{session_id}",
            "--as",
            "trajectory",
            "--out",
            str(exports),
        ],
        "session_json": [
            *base,
            "--no-sync",
            "export",
            "{session_id}",
            "--as",
            "json",
            "--out",
            str(exports),
        ],
        "replay": [
            *base,
            "--no-sync",
            "distill",
            "replay",
            "{session_id}",
            "--out",
            str(evidence_dir / "replay.sh"),
        ],
    }


def run_command(
    command: list[str],
    cwd: Path,
    timeout: int,
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env or os.environ.copy(),
    )
    if check and completed.returncode != 0:
        rendered = " ".join(command[:8])
        raise EvaluationError(
            f"Command failed ({completed.returncode}): {rendered}\n"
            f"{completed.stderr[-4000:]}"
        )
    return completed


def harness_environment(
    report_dir: Path, base: dict[str, str] | None = None
) -> dict[str, str]:
    environment = dict(base or os.environ)
    zdotdir = report_dir / "harness-zdotdir"
    zdotdir.mkdir(parents=True, exist_ok=True)
    environment["ZDOTDIR"] = str(zdotdir)
    environment["BASH_ENV"] = "/dev/null"
    environment["NO_COLOR"] = "1"
    return environment


def git_output(workspace: Path, *args: str) -> str:
    return run_command(["git", *args], workspace, 120).stdout.strip()


def repository_slug(remote: str) -> str:
    normalized = remote.removesuffix(".git")
    if normalized.startswith("git@github.com:"):
        return normalized.split(":", 1)[1]
    marker = "github.com/"
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    raise EvaluationError(f"Unsupported GitHub remote: {remote}")


def verify_publication_preconditions(
    repo_dir: Path, expected_repo: str, expected_login: str
) -> None:
    if git_output(repo_dir, "status", "--porcelain=v1"):
        raise EvaluationError(f"Fixture checkout is not clean: {repo_dir}")
    actual_repo = repository_slug(git_output(repo_dir, "remote", "get-url", "origin"))
    if actual_repo.casefold() != expected_repo.casefold():
        raise EvaluationError(
            f"Fixture remote is {actual_repo}; expected {expected_repo}"
        )
    actual_login = run_command(
        ["gh", "api", "user", "--jq", ".login"], repo_dir, 120
    ).stdout.strip()
    if actual_login != expected_login:
        raise EvaluationError(
            f"Active GitHub login is {actual_login}; expected {expected_login}"
        )


def install_workflow(workspace: Path, harness: str) -> None:
    run_command(
        [
            sys.executable,
            str(ROOT / "scripts" / "skill-package.py"),
            "install",
            "--scope",
            "project",
            "--project-dir",
            str(workspace),
            "--harness",
            harness,
            "--skill",
            "charlies-workflow",
        ],
        ROOT,
        300,
    )


def status_changes(workspace: Path) -> list[str]:
    output = git_output(
        workspace, "status", "--porcelain=v1", "--untracked-files=all"
    )
    return [line for line in output.splitlines() if line]


def _status_path(change: str) -> str:
    path = change[3:] if len(change) > 3 else change
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[1]
    return path.strip('"')


def unexpected_preimplementation_changes(workspace: Path) -> list[str]:
    return [
        change
        for change in status_changes(workspace)
        if not any(_status_path(change).startswith(prefix) for prefix in IGNORED_EVAL_PREFIXES)
    ]


def has_temporary_artifacts(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file() or path.is_symlink():
        return True
    return any(item.is_file() or item.is_symlink() for item in path.rglob("*"))


def assistant_output(harness: str, transcript: str) -> str:
    messages: list[str] = []
    claude_result: str | None = None
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if harness == "codex" and event.get("type") == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") in {
                "agent_message",
                "message",
            }:
                text = item.get("text")
                if isinstance(text, str):
                    messages.append(text)
        elif harness == "claude" and event.get("type") == "result":
            result = event.get("result")
            if isinstance(result, str):
                claude_result = result
        elif harness == "claude" and event.get("type") == "assistant":
            message = event.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text")
                        if isinstance(text, str):
                            messages.append(text)
    if harness == "claude" and claude_result is not None:
        return claude_result
    return "\n".join(messages)


def copy_checkpoint_artifacts(
    workspace: Path, report_dir: Path, turn_number: int, turn_id: str
) -> list[str]:
    source = workspace / "output" / "workflow"
    destination = report_dir / "checkpoints" / f"{turn_number:02d}-{turn_id}"
    if not source.is_dir():
        return []
    shutil.copytree(source, destination, dirs_exist_ok=True)
    return sorted(
        path.relative_to(report_dir).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    )


def evaluate_turn(
    turn: dict[str, Any],
    assistant_text: str,
    workspace: Path,
    artifact_paths: list[str],
) -> list[str]:
    failures: list[str] = []
    text = assistant_text
    workflow_root = workspace / "output" / "workflow"
    artifact_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(workflow_root.rglob("*.md"))
        if path.is_file()
    ) if workflow_root.is_dir() else ""
    evidence_text = f"{text}\n{artifact_text}".replace("\u00d7", "x")
    expected = turn["expected_phase"]
    if re.search(
        rf"(?i)workflow phase:\s*{re.escape(expected)}", text
    ) is None:
        failures.append(f"missing exact phase marker: {expected}")
    if turn["forbid_source_changes"]:
        changes = unexpected_preimplementation_changes(workspace)
        if changes:
            failures.append(f"source changed before implementation: {changes}")
    if turn["id"] == "discovery":
        if "?" not in text and re.search(r"(?i)(question|pregunta|decision)", text) is None:
            failures.append("discovery did not ask a meaningful question")
        if not any(path.endswith("/run-state.json") for path in artifact_paths):
            failures.append("discovery did not create the canonical run-state.json")
    if turn["id"] == "spec":
        if not artifact_paths:
            failures.append("spec checkpoint produced no workflow artifact")
        if re.search(
            r"(?i)(acceptance criteria|criterios de aceptaci)", evidence_text
        ) is None:
            failures.append("spec output omitted acceptance criteria")
    if turn["id"] == "plan":
        markdown = [path for path in artifact_paths if path.endswith(".md")]
        if len(markdown) < 2:
            failures.append("plan checkpoint did not preserve distinct spec and plan files")
        for pattern, label in (
            (r"(?i)(red|green|tdd)", "TDD evidence"),
            (r"390x844", "small-mobile viewport"),
            (r"768x1024", "tablet viewport"),
            (r"1440x900", "desktop viewport"),
        ):
            if re.search(pattern, evidence_text) is None:
                failures.append(f"plan output omitted {label}")
    return failures


def run_turn(
    harness: str,
    workspace: Path,
    turn: dict[str, Any],
    turn_number: int,
    session_id: str | None,
    report_dir: Path,
    timeout: int,
    additional_writable: Path | None,
    environment: dict[str, str],
) -> tuple[str, str, str]:
    if turn_number == 1:
        command = build_initial_command(
            harness,
            workspace,
            turn["prompt"],
            session_id,
            additional_writable,
        )
    else:
        if session_id is None:
            raise EvaluationError("Cannot resume without a session id")
        command = build_resume_command(
            harness,
            workspace,
            session_id,
            turn["prompt"],
            additional_writable,
        )
    completed = run_command(
        command, workspace, timeout, check=False, env=environment
    )
    transcript = "\n".join(
        part for part in (completed.stdout, completed.stderr) if part
    )
    turn_dir = report_dir / "turns"
    turn_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = turn_dir / f"{turn_number:02d}-{turn['id']}.jsonl"
    transcript_path.write_text(transcript + "\n", encoding="utf-8")
    if completed.returncode != 0:
        raise EvaluationError(
            f"{harness} turn {turn['id']} exited {completed.returncode}; "
            f"see {transcript_path}"
        )
    if harness == "codex" and session_id is None:
        session_id = extract_codex_session_id(completed.stdout)
    if session_id is None:
        raise EvaluationError("Harness session id is unavailable")
    return session_id, transcript, assistant_output(harness, completed.stdout)


def run_verification_commands(workspace: Path, report_dir: Path) -> list[dict[str, Any]]:
    commands = [
        ["corepack", "pnpm", "test"],
        ["corepack", "pnpm", "lint"],
        ["corepack", "pnpm", "build"],
    ]
    results: list[dict[str, Any]] = []
    for index, command in enumerate(commands, start=1):
        started = time.monotonic()
        completed = run_command(command, workspace, 600, check=False)
        duration_ms = round((time.monotonic() - started) * 1000)
        log = report_dir / "verification" / f"{index:02d}-{command[-1]}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        results.append(
            {
                "command": command,
                "returncode": completed.returncode,
                "duration_ms": duration_ms,
                "log": log.relative_to(report_dir).as_posix(),
            }
        )
    return results


def wait_for_server(url: str, timeout: int = 60) -> None:
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except OSError:
            time.sleep(0.25)
    raise EvaluationError(f"Development server did not become ready: {url}")


def run_browser_oracle(workspace: Path, report_dir: Path, port: int) -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{port}"
    server_log = report_dir / "browser" / "server.log"
    screenshots = report_dir / "browser" / "screenshots"
    server_log.parent.mkdir(parents=True, exist_ok=True)
    oracle_copy = workspace / "output" / "e2e-oracle.mjs"
    oracle_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ORACLE_PATH, oracle_copy)
    started = time.monotonic()
    with server_log.open("w", encoding="utf-8") as handle:
        server = subprocess.Popen(
            [
                "corepack",
                "pnpm",
                "dev",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--strictPort",
            ],
            cwd=workspace,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_for_server(base_url)
            completed = run_command(
                ["node", str(oracle_copy), base_url, str(screenshots)],
                workspace,
                300,
                check=False,
            )
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
            oracle_copy.unlink(missing_ok=True)
    oracle_log = report_dir / "browser" / "oracle.log"
    oracle_log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    return {
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "log": oracle_log.relative_to(report_dir).as_posix(),
        "screenshots": sorted(
            path.relative_to(report_dir).as_posix()
            for path in screenshots.glob("*.png")
        ),
    }


def git_diff_summary(workspace: Path, base_ref: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    additions = 0
    deletions = 0
    output = git_output(workspace, "diff", "--numstat", f"{base_ref}...HEAD")
    for line in output.splitlines():
        added, deleted, path = line.split("\t", 2)
        numeric_added = int(added) if added.isdigit() else 0
        numeric_deleted = int(deleted) if deleted.isdigit() else 0
        additions += numeric_added
        deletions += numeric_deleted
        rows.append(
            {
                "path": path,
                "additions": numeric_added,
                "deletions": numeric_deleted,
            }
        )
    return {
        "files": len(rows),
        "additions": additions,
        "deletions": deletions,
        "paths": rows,
    }


def find_draft_pr(expected_repo: str, branch: str, workspace: Path) -> dict[str, Any]:
    completed = run_command(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            expected_repo,
            "--head",
            branch,
            "--state",
            "open",
            "--json",
            "number,url,isDraft,state,headRefOid,baseRefName",
        ],
        workspace,
        120,
    )
    rows = json.loads(completed.stdout)
    if len(rows) != 1:
        raise EvaluationError(f"Expected one open PR for {branch}; found {len(rows)}")
    return rows[0]


def run_decant(session_log: Path, evidence_dir: Path) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    plan = build_decant_plan(session_log, evidence_dir)
    outputs: dict[str, str] = {}
    datasets: dict[str, Any] = {}
    sync = run_command(plan["sync"], ROOT, 600, check=False)
    (evidence_dir / "sync.json").write_text(
        sync.stdout + sync.stderr, encoding="utf-8"
    )
    if sync.returncode not in (0, 3):
        raise EvaluationError(f"Decant sync failed with exit {sync.returncode}")

    sessions = run_command(plan["sessions"], ROOT, 300)
    (evidence_dir / "sessions.json").write_text(sessions.stdout, encoding="utf-8")
    rows = json.loads(sessions.stdout)
    if len(rows) != 1:
        raise EvaluationError(
            f"Decant isolated archive contains {len(rows)} sessions; expected one"
        )
    decant_session_id = str(rows[0]["id"])

    for name in ("stats", "economics", "files", "tools", "mcp"):
        completed = run_command(plan[name], ROOT, 300)
        output = evidence_dir / f"{name}.json"
        output.write_text(completed.stdout, encoding="utf-8")
        outputs[name] = output.name
        datasets[name] = json.loads(completed.stdout)

    for name in ("trajectory", "session_json", "replay"):
        command = [
            decant_session_id if part == "{session_id}" else part
            for part in plan[name]
        ]
        run_command(command, ROOT, 300)

    files = datasets.get("files") if isinstance(datasets.get("files"), list) else []
    sync_payload = json.loads(sync.stdout) if sync.stdout.strip() else {}
    return {
        "version": DECANT_VERSION,
        "source_log": str(session_log),
        "session_id": decant_session_id,
        "session": rows[0],
        "outputs": outputs,
        "stats": datasets.get("stats", []),
        "economics": datasets.get("economics", {}),
        "tools": datasets.get("tools", []),
        "mcp": datasets.get("mcp", []),
        "files": {
            "rows": len(files),
            "reads": sum(int(item.get("reads") or 0) for item in files),
            "edits": sum(int(item.get("edits") or 0) for item in files),
            "writes": sum(int(item.get("writes") or 0) for item in files),
            "deletes": sum(int(item.get("deletes") or 0) for item in files),
            "top_paths": [
                {
                    "path": item.get("key"),
                    "reads": int(item.get("reads") or 0),
                    "edits": int(item.get("edits") or 0),
                    "writes": int(item.get("writes") or 0),
                }
                for item in files[:10]
            ],
        },
        "ingest": {
            "issues": int(sync_payload.get("issues") or 0),
            "issues_by_code": sync_payload.get("issues_by_code", {}),
            "failed": int(sync_payload.get("failed") or 0),
        },
        "trajectory": f"exports/{decant_session_id}.trajectory.json",
        "session_json": f"exports/{decant_session_id}.json",
        "replay": "replay.sh",
    }


def _format_number(value: Any) -> str:
    return f"{int(value or 0):,}"


def _format_duration(milliseconds: Any) -> str:
    total_ms = int(milliseconds or 0)
    minutes, remainder = divmod(total_ms, 60_000)
    seconds = remainder / 1000
    if minutes:
        return f"{minutes}m {seconds:04.1f}s"
    return f"{seconds:.1f}s"


def _format_cost(value: Any) -> str:
    return "not reported" if value is None else f"${float(value):.4f}"


def _append_table(
    lines: list[str], headers: list[str], rows: list[list[str]]
) -> None:
    if not rows:
        lines.append("No rows reported.")
        return
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    lines.extend("| " + " | ".join(row) + " |" for row in rows)


def _usage_discrepancies(report: dict[str, Any]) -> list[str]:
    native = report.get("native")
    decant = report.get("decant")
    if not isinstance(native, dict) or not isinstance(decant, dict):
        return []
    native_tokens = native.get("tokens", {})
    decant_session = decant.get("session", {})
    differences: list[str] = []
    native_output = int(native_tokens.get("output_tokens") or 0)
    decant_output = int(decant_session.get("total_output_tokens") or 0)
    if native_output != decant_output:
        differences.append(
            f"output tokens: native {_format_number(native_output)} vs "
            f"Decant {_format_number(decant_output)}"
        )
    native_input_key = (
        "uncached_input_tokens"
        if report.get("harness") == "codex"
        else "input_tokens"
    )
    native_input = int(native_tokens.get(native_input_key) or 0)
    decant_input = int(decant_session.get("total_input_tokens") or 0)
    if native_input != decant_input:
        differences.append(
            f"direct input tokens: native {_format_number(native_input)} vs "
            f"Decant {_format_number(decant_input)}"
        )
    native_cost = native.get("native_cost_usd")
    decant_cost = decant_session.get("estimated_cost_usd")
    if native_cost is not None and decant_cost is not None:
        if abs(float(native_cost) - float(decant_cost)) >= 0.0001:
            differences.append(
                f"cost: native {_format_cost(native_cost)} vs "
                f"Decant estimate {_format_cost(decant_cost)}"
            )
    return differences


def write_report(report_dir: Path, report: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    native = report.get("native") if isinstance(report.get("native"), dict) else {}
    native_session = (
        native.get("session") if isinstance(native.get("session"), dict) else {}
    )
    native_tokens = (
        native.get("tokens") if isinstance(native.get("tokens"), dict) else {}
    )
    decant = report.get("decant") if isinstance(report.get("decant"), dict) else {}
    decant_session = (
        decant.get("session") if isinstance(decant.get("session"), dict) else {}
    )
    lines = [
        f"# {report['harness'].title()} lifecycle evaluation",
        "",
        f"- Status: {'PASS' if report['passed'] else 'FAIL'}",
        f"- Session: `{report.get('session_id', 'unavailable')}`",
        f"- Branch: `{report['branch']}`",
        f"- Draft PR: {report.get('pull_request', {}).get('url', 'missing')}",
        f"- Decant: {decant.get('version', 'not-run')}",
        "",
        "## Runtime and models",
        "",
    ]
    _append_table(
        lines,
        ["Measure", "Value"],
        [
            ["Harness version", f"`{native.get('harness_version', 'unknown')}`"],
            ["Native model", f"`{native.get('model', 'unknown')}`"],
            [
                "Reasoning effort",
                f"`{native.get('reasoning_effort') or 'not exposed'}`",
            ],
            ["Session wall time", _format_duration(native_session.get("wall_time_ms"))],
            ["Turn-active time", _format_duration(native_session.get("turn_active_ms"))],
            ["Inter-turn gap", _format_duration(native_session.get("inter_turn_gap_ms"))],
            ["Messages parsed by Decant", _format_number(decant_session.get("message_count"))],
            [
                "Context window / peak",
                f"{_format_number(decant_session.get('context_window_tokens') or native_session.get('context_window_tokens'))} / "
                f"{_format_number(decant_session.get('peak_context_tokens') or native_session.get('peak_context_tokens'))}",
            ],
            ["Compactions", _format_number(decant_session.get("compaction_count"))],
            ["Subagents", _format_number(decant_session.get("subagent_count"))],
        ],
    )
    model_usage = native.get("model_usage")
    if isinstance(model_usage, dict) and model_usage:
        lines.extend(["", "Native per-model usage:", ""])
        _append_table(
            lines,
            ["Model", "Input", "Cache read", "Cache write", "Output", "Cost"],
            [
                [
                    f"`{name}`",
                    _format_number(values.get("inputTokens")),
                    _format_number(values.get("cacheReadInputTokens")),
                    _format_number(values.get("cacheCreationInputTokens")),
                    _format_number(values.get("outputTokens")),
                    _format_cost(values.get("costUSD")),
                ]
                for name, values in model_usage.items()
                if isinstance(values, dict)
            ],
        )

    lines.extend(["", "## Native token accounting", ""])
    token_rows = [
        [label, _format_number(native_tokens.get(field))]
        for field, label in (
            ("input_tokens", "Input tokens reported"),
            ("cached_input_tokens", "Cached input tokens"),
            ("uncached_input_tokens", "Uncached input tokens"),
            ("cache_creation_input_tokens", "Cache creation input tokens"),
            ("cache_read_input_tokens", "Cache read input tokens"),
            ("output_tokens", "Output tokens"),
            ("reasoning_output_tokens", "Reasoning output tokens"),
        )
        if field in native_tokens
    ]
    _append_table(lines, ["Token measure", "Native total"], token_rows)
    lines.extend(
        [
            "",
            f"Native harness cost: **{_format_cost(native.get('native_cost_usd'))}**. "
            f"Decant estimate: **{_format_cost(decant_session.get('estimated_cost_usd'))}**.",
        ]
    )
    decant_stats = decant.get("stats") if isinstance(decant.get("stats"), list) else []
    if decant_stats:
        lines.append(
            "Decant model rollup: "
            + ", ".join(
                f"`{item.get('key', 'unknown')}` with "
                f"{_format_number(item.get('reasoning_tokens'))} reported and "
                f"{_format_number(item.get('est_reasoning_tokens'))} estimated reasoning tokens"
                for item in decant_stats
            )
            + "."
        )
    differences = _usage_discrepancies(report)
    if differences:
        lines.append(
            "**Caution: Decant differs from native telemetry** - "
            + "; ".join(differences)
            + "."
        )

    lines.extend(["", "## Per-turn telemetry", ""])
    turn_rows: list[list[str]] = []
    for turn in native.get("turns", []):
        usage = turn.get("usage", {})
        cache_read = usage.get(
            "cached_input_tokens", usage.get("cache_read_input_tokens", 0)
        )
        cache_write = usage.get(
            "cache_write_input_tokens", usage.get("cache_creation_input_tokens", 0)
        )
        turn_rows.append(
            [
                str(turn.get("id", "unknown")),
                _format_duration(turn.get("duration_ms")),
                _format_duration(turn.get("api_duration_ms"))
                if "api_duration_ms" in turn
                else "n/a",
                _format_number(turn.get("model_turns"))
                if "model_turns" in turn
                else "n/a",
                _format_number(usage.get("input_tokens")),
                _format_number(cache_read),
                _format_number(cache_write),
                _format_number(usage.get("output_tokens")),
                _format_number(usage.get("reasoning_output_tokens"))
                if "reasoning_output_tokens" in usage
                else "n/a",
                _format_number(turn.get("tool_calls")),
                _format_cost(turn.get("native_cost_usd"))
                if "native_cost_usd" in turn
                else "n/a",
            ]
        )
    _append_table(
        lines,
        [
            "Stage",
            "Wall",
            "API",
            "Model turns",
            "Input",
            "Cache read",
            "Cache write",
            "Output",
            "Reasoning",
            "Tools",
            "Native cost",
        ],
        turn_rows,
    )

    lines.extend(["", "## Tool calls", ""])
    native_tools = native.get("tools", {})
    lines.append(
        f"Native log: **{_format_number(native_tools.get('total_calls'))} calls**, "
        f"**{_format_number(native_tools.get('errors'))} errors**."
    )
    _append_table(
        lines,
        ["Native tool", "Calls"],
        [
            [name, _format_number(calls)]
            for name, calls in native_tools.get("by_name", {}).items()
        ],
    )
    decant_tools = decant.get("tools") if isinstance(decant.get("tools"), list) else []
    lines.extend(["", "Decant latency view:", ""])
    _append_table(
        lines,
        ["Decant tool", "Calls", "Errors", "p50", "p95"],
        [
            [
                str(item.get("tool_name", "unknown")),
                _format_number(item.get("calls")),
                _format_number(item.get("errors")),
                f"{_format_number(item.get('p50_ms'))} ms",
                f"{_format_number(item.get('p95_ms'))} ms",
            ]
            for item in decant_tools
        ],
    )
    mcp = decant.get("mcp") if isinstance(decant.get("mcp"), list) else []
    lines.append(f"\nMCP calls recorded by Decant: **{sum(int(item.get('calls') or 0) for item in mcp)}**.")

    economics = decant.get("economics")
    if isinstance(economics, dict):
        lines.extend(["", "## Decant economics and time attribution", ""])
        buckets = economics.get("buckets") if isinstance(economics.get("buckets"), list) else []
        _append_table(
            lines,
            ["Bucket", "Generation", "Context", "Calls", "Active", "Cost", "Share"],
            [
                [
                    str(bucket.get("bucket", "unknown")),
                    _format_number(bucket.get("generation_tokens")),
                    _format_number(bucket.get("context_window_tokens")),
                    _format_number(bucket.get("tool_calls")),
                    _format_duration(bucket.get("active_ms")),
                    _format_cost(bucket.get("estimated_cost_usd")),
                    f"{float(bucket.get('cost_share') or 0) * 100:.1f}%",
                ]
                for bucket in buckets
            ],
        )
        totals = economics.get("totals") if isinstance(economics.get("totals"), dict) else {}
        lines.append(
            "\nDecant attributed "
            f"{_format_duration(totals.get('active_ms'))} active and "
            f"{_format_duration(totals.get('waiting_on_user_ms'))} waiting on the user. "
            "These are attribution estimates and can overlap wall-clock intervals."
        )
        phases = totals.get("phases") if isinstance(totals.get("phases"), dict) else {}
        if phases:
            lines.extend(["", "Decant phase attribution:", ""])
            _append_table(
                lines,
                ["Phase", "Generation", "Context", "Active", "Cost"],
                [
                    [
                        str(name),
                        _format_number(values.get("generation_tokens")),
                        _format_number(values.get("context_window_tokens")),
                        _format_duration(values.get("active_ms")),
                        _format_cost(values.get("estimated_cost_usd")),
                    ]
                    for name, values in phases.items()
                    if isinstance(values, dict)
                ],
            )
            implementation = phases.get("implementation")
            if isinstance(implementation, dict) and not int(
                implementation.get("generation_tokens") or 0
            ):
                lines.append(
                    "\nDecant assigned zero generation tokens to implementation; "
                    "do not use its phase split for this run."
                )

    files = decant.get("files") if isinstance(decant.get("files"), dict) else {}
    lines.extend(["", "## File activity", ""])
    lines.append(
        "Decant emitted "
        f"**{_format_number(files.get('rows'))} path rows**: "
        f"{_format_number(files.get('reads'))} reads, "
        f"{_format_number(files.get('edits'))} edits, "
        f"{_format_number(files.get('writes'))} writes, and "
        f"{_format_number(files.get('deletes'))} deletes."
    )

    lines.extend(["", "## Gates", ""])
    for gate in report.get("gates", []):
        lines.append(
            f"- {gate['id']}: {'PASS' if gate['passed'] else 'FAIL'}"
            + (f" ({'; '.join(gate['failures'])})" if gate["failures"] else "")
        )
    corrections = report.get("evaluation_corrections")
    if isinstance(corrections, list) and corrections:
        lines.extend(["", "Evaluation corrections:"])
        lines.extend(f"- {correction}" for correction in corrections)
    lines.extend(["", "## Independent verification", ""])
    for item in report.get("verification", []):
        duration = (
            f" in {_format_duration(item.get('duration_ms'))}"
            if "duration_ms" in item
            else ""
        )
        lines.append(
            f"- `{' '.join(item['command'])}`: exit {item['returncode']}{duration}"
        )
    browser = report.get("browser", {})
    lines.append(
        f"- Browser oracle: {'PASS' if browser.get('passed') else 'FAIL'}"
        + (
            f" in {_format_duration(browser.get('duration_ms'))}"
            if "duration_ms" in browser
            else ""
        )
    )
    for screenshot in browser.get("screenshots", []):
        lines.append(f"- Screenshot: `{screenshot}`")

    product_diff = report.get("product_diff")
    if isinstance(product_diff, dict):
        lines.extend(["", "## Delivery footprint", ""])
        lines.append(
            f"Product diff: **{_format_number(product_diff.get('files'))} files**, "
            f"**+{_format_number(product_diff.get('additions'))}"
            f"/-{_format_number(product_diff.get('deletions'))}**."
        )

    ingest = decant.get("ingest") if isinstance(decant.get("ingest"), dict) else {}
    lines.extend(["", "## Interpretation limits", ""])
    lines.append(
        f"- Decant ingest issues: {_format_number(ingest.get('issues'))}; "
        f"failed records: {_format_number(ingest.get('failed'))}."
    )
    lines.append(
        "- Cost is an estimate unless the native harness reports a cost; subscription billing is not inferred."
    )
    lines.append(
        "- Native and Decant token fields have different cache semantics; use the discrepancy callout above before comparing harnesses."
    )
    lines.append(
        "- Transcripts, Decant databases, exports, and screenshots are local evidence and must not be committed."
    )
    lines.append("")
    (report_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=("codex", "claude"), required=True)
    parser.add_argument("--repo-dir", type=Path, required=True)
    parser.add_argument("--base-ref", default="fixture-v2")
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--port", type=int, default=4317)
    parser.add_argument("--keep-worktree", action="store_true")
    parser.add_argument("--skip-decant", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario = load_scenario()
    publication = scenario["publication"]
    repo_dir = args.repo_dir.expanduser().resolve()
    verify_publication_preconditions(
        repo_dir, publication["repository"], publication["github_login"]
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_dir = (
        args.report_dir.expanduser().resolve()
        if args.report_dir
        else ROOT / "output" / "e2e" / f"{run_id}-{args.harness}"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    branch = f"e2e/{args.harness}-{run_id.lower()}"
    report: dict[str, Any] = {
        "schema_version": 1,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "harness": args.harness,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture_repository": publication["repository"],
        "base_ref": args.base_ref,
        "branch": branch,
        "gates": [],
        "passed": False,
    }

    temporary: tempfile.TemporaryDirectory[str] | None = None
    branch_created = False
    if args.keep_worktree:
        temporary_root = Path(
            tempfile.mkdtemp(prefix=f"charlie-e2e-{args.harness}-")
        )
    else:
        temporary = tempfile.TemporaryDirectory(
            prefix=f"charlie-e2e-{args.harness}-"
        )
        temporary_root = Path(temporary.name)
    workspace = temporary_root / "workspace"
    try:
        run_command(
            ["git", "fetch", "origin", "--prune", "--tags"], repo_dir, 300
        )
        run_command(
            ["git", "worktree", "add", str(workspace), "-b", branch, args.base_ref],
            repo_dir,
            300,
        )
        branch_created = True
        install_workflow(workspace, args.harness)
        run_command(["corepack", "pnpm", "install", "--frozen-lockfile"], workspace, 900)
        git_common_raw = git_output(workspace, "rev-parse", "--git-common-dir")
        git_common = Path(git_common_raw)
        if not git_common.is_absolute():
            git_common = (workspace / git_common).resolve()

        baseline = run_verification_commands(workspace, report_dir / "baseline")
        if any(item["returncode"] != 0 for item in baseline):
            raise EvaluationError("Fixture baseline verification failed")
        report["baseline"] = baseline
        environment = harness_environment(report_dir)

        session_id = str(uuid.uuid4()) if args.harness == "claude" else None
        turn_transcripts: list[dict[str, str]] = []
        for turn_number, turn in enumerate(scenario["turns"], start=1):
            session_id, transcript, assistant_text = run_turn(
                args.harness,
                workspace,
                turn,
                turn_number,
                session_id,
                report_dir,
                args.timeout,
                git_common,
                environment,
            )
            turn_transcripts.append({"id": turn["id"], "transcript": transcript})
            report["session_id"] = session_id
            artifact_paths = copy_checkpoint_artifacts(
                workspace, report_dir, turn_number, turn["id"]
            )
            failures = evaluate_turn(
                turn, assistant_text, workspace, artifact_paths
            )
            report["gates"].append(
                {
                    "id": turn["id"],
                    "expected_phase": turn["expected_phase"],
                    "passed": not failures,
                    "failures": failures,
                    "artifacts": artifact_paths,
                }
            )
            if failures:
                raise EvaluationError(
                    f"Lifecycle gate {turn['id']} failed: {'; '.join(failures)}"
                )
        report["session_id"] = session_id

        verification = run_verification_commands(workspace, report_dir)
        report["verification"] = verification
        browser = run_browser_oracle(workspace, report_dir, args.port)
        report["browser"] = browser

        pull_request = find_draft_pr(publication["repository"], branch, workspace)
        report["pull_request"] = pull_request
        final_head = git_output(workspace, "rev-parse", "HEAD")
        report["final_head"] = final_head
        report["product_diff"] = git_diff_summary(workspace, args.base_ref)
        publication_failures = []
        if not pull_request["isDraft"]:
            publication_failures.append("PR is not draft")
        if pull_request["baseRefName"] != publication["base"]:
            publication_failures.append("PR base is not main")
        if pull_request["headRefOid"] != final_head:
            publication_failures.append("PR head does not match the final local HEAD")
        if has_temporary_artifacts(workspace / "output" / "workflow"):
            publication_failures.append("temporary workflow artifacts remain after publication")
        if any(item["returncode"] != 0 for item in verification):
            publication_failures.append("one or more independent verification commands failed")
        if not browser["passed"]:
            publication_failures.append("independent browser oracle failed")
        report["gates"].append(
            {
                "id": "independent-verification-and-publication",
                "passed": not publication_failures,
                "failures": publication_failures,
                "artifacts": browser["screenshots"],
            }
        )

        session_log = find_session_log(args.harness, session_id, Path.home())
        if args.harness == "codex":
            report["native"] = parse_codex_native_telemetry(
                session_log, [turn["id"] for turn in scenario["turns"]]
            )
        else:
            report["native"] = parse_claude_native_telemetry(
                session_log, turn_transcripts
            )
        if not args.skip_decant:
            report["decant"] = run_decant(session_log, report_dir / "decant")

        report["passed"] = all(gate["passed"] for gate in report["gates"])
        write_report(report_dir, report)
        print(f"{'PASS' if report['passed'] else 'FAIL'} {args.harness}: {report_dir}")
        return 0 if report["passed"] else 1
    except (EvaluationError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
        report["passed"] = False
        write_report(report_dir, report)
        print(f"FAIL {args.harness}: {error}", file=sys.stderr)
        print(f"Evidence: {report_dir}", file=sys.stderr)
        return 1
    finally:
        if workspace.exists() and not args.keep_worktree:
            run_command(
                ["git", "worktree", "remove", "--force", str(workspace)],
                repo_dir,
                300,
                check=False,
            )
        if branch_created and not args.keep_worktree:
            run_command(
                ["git", "branch", "-D", branch],
                repo_dir,
                120,
                check=False,
            )
        if args.keep_worktree:
            print(f"Worktree retained: {workspace}")
        elif temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
