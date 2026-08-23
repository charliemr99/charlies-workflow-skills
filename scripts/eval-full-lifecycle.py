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
        completed = run_command(command, workspace, 600, check=False)
        log = report_dir / "verification" / f"{index:02d}-{command[-1]}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        results.append(
            {
                "command": command,
                "returncode": completed.returncode,
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
        "log": oracle_log.relative_to(report_dir).as_posix(),
        "screenshots": sorted(
            path.relative_to(report_dir).as_posix()
            for path in screenshots.glob("*.png")
        ),
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

    for name in ("economics", "files", "tools", "mcp"):
        completed = run_command(plan[name], ROOT, 300)
        output = evidence_dir / f"{name}.json"
        output.write_text(completed.stdout, encoding="utf-8")
        outputs[name] = output.name

    for name in ("trajectory", "session_json", "replay"):
        command = [
            decant_session_id if part == "{session_id}" else part
            for part in plan[name]
        ]
        run_command(command, ROOT, 300)

    return {
        "version": DECANT_VERSION,
        "source_log": str(session_log),
        "session_id": decant_session_id,
        "session": rows[0],
        "outputs": outputs,
        "trajectory": f"exports/{decant_session_id}.trajectory.json",
        "session_json": f"exports/{decant_session_id}.json",
        "replay": "replay.sh",
    }


def write_report(report_dir: Path, report: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        f"# {report['harness'].title()} lifecycle evaluation",
        "",
        f"- Status: {'PASS' if report['passed'] else 'FAIL'}",
        f"- Session: `{report.get('session_id', 'unavailable')}`",
        f"- Branch: `{report['branch']}`",
        f"- Draft PR: {report.get('pull_request', {}).get('url', 'missing')}",
        f"- Decant: {report.get('decant', {}).get('version', 'not-run')}",
        "",
        "## Gates",
        "",
    ]
    for gate in report.get("gates", []):
        lines.append(
            f"- {gate['id']}: {'PASS' if gate['passed'] else 'FAIL'}"
            + (f" ({'; '.join(gate['failures'])})" if gate["failures"] else "")
        )
    lines.extend(
        [
            "",
            "## Verification",
            "",
            *[
                f"- `{' '.join(item['command'])}`: exit {item['returncode']}"
                for item in report.get("verification", [])
            ],
            f"- Browser oracle: {'PASS' if report.get('browser', {}).get('passed') else 'FAIL'}",
            "",
            "Transcripts and Decant exports are local evidence and must not be committed.",
            "",
        ]
    )
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

        if not args.skip_decant:
            session_log = find_session_log(
                args.harness, session_id, Path.home()
            )
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
