#!/usr/bin/env python3
"""Run opt-in behavioral smoke evaluations for Charlie's Workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "charlies-workflow-cases.json"
TEMPORARY_OUTPUT_PREFIXES = ("output/workflow/",)
PHASE_PATTERNS = {
    "awaiting-discovery-answer": r"(?i)(question|pregunta|clarif|decision|decisi)",
    "awaiting-spec-approval": r"(?i)(spec|brief).{0,120}(approval|approve|aprob)",
    "plan-ready": r"(?i)(implementation plan|plan de implementaci)",
}
EVIDENCE_BOUNDARY = "model-driven-smoke-evaluation"
CLAUDE_SKILL_SYSTEM_PROMPT = (
    "The user explicitly invoked the project-scoped charlies-workflow skill. "
    "Before any task action, load charlies-workflow with the Skill tool and "
    "follow it for the entire session."
)
INVOCATIONS = {
    "codex": "$charlies-workflow",
    "claude": "/charlies-workflow",
    "custom": "$charlies-workflow",
}


def load_cases() -> list[dict[str, Any]]:
    document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if document.get("schema_version") != 2:
        raise ValueError("Unsupported behavioral eval schema")
    if document.get("evidence_boundary") != EVIDENCE_BOUNDARY:
        raise ValueError(
            f"Behavioral eval evidence_boundary must be {EVIDENCE_BOUNDARY}"
        )
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Behavioral eval suite has no cases")
    required_keys = {
        "id",
        "prompt",
        "expected_phase",
        "required_output",
        "forbidden_output",
        "forbid_workspace_changes",
        "required_artifacts",
    }
    for case in cases:
        if not isinstance(case, dict) or not required_keys.issubset(case):
            raise ValueError("Behavioral eval case has an invalid shape")
        if case["expected_phase"] not in PHASE_PATTERNS:
            raise ValueError(
                f"Unsupported expected phase: {case['expected_phase']}"
            )
    return cases


def run_checked(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def render_prompt(harness: str, prompt: str) -> str:
    return prompt.replace("{{workflow}}", INVOCATIONS[harness])


def install_workflow(workspace: Path, harness: str) -> None:
    run_checked(
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
    )


def create_fixture(
    harness: str, install_skill: bool = True
) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory(prefix="charlies-workflow-eval-")
    workspace = Path(temporary.name)
    (workspace / "src").mkdir()
    (workspace / "tests").mkdir()
    (workspace / "src" / "app.js").write_text(
        "export function visibleRows(rows) { return rows; }\n",
        encoding="utf-8",
    )
    (workspace / "tests" / "app.test.js").write_text(
        "// Fixture test surface.\n",
        encoding="utf-8",
    )
    (workspace / "README.md").write_text(
        "# Workflow evaluation fixture\n\nA small established JavaScript app.\n",
        encoding="utf-8",
    )
    (workspace / ".gitignore").write_text("output/\n", encoding="utf-8")

    if install_skill:
        install_workflow(workspace, harness)

    run_checked(["git", "init", "-q"], workspace)
    run_checked(["git", "config", "user.email", "workflow-eval@example.invalid"], workspace)
    run_checked(["git", "config", "user.name", "Workflow Eval"], workspace)
    run_checked(["git", "add", "."], workspace)
    run_checked(["git", "commit", "-qm", "fixture"], workspace)
    return temporary, workspace


def build_command(
    harness: str,
    workspace: Path,
    prompt: str,
    command_template: str | None,
) -> list[str]:
    prompt = render_prompt(harness, prompt)
    prompt_path = workspace.parent / f"{workspace.name}-eval-prompt.txt"
    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    if command_template:
        values = {
            "workspace": str(workspace),
            "prompt": prompt,
            "prompt_file": str(prompt_path),
        }
        return [part.format(**values) for part in shlex.split(command_template)]
    if harness == "codex":
        return [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--color",
            "never",
            "-C",
            str(workspace),
            prompt,
        ]
    if harness == "claude":
        return [
            "claude",
            "-p",
            "--permission-mode",
            "dontAsk",
            "--append-system-prompt",
            CLAUDE_SKILL_SYSTEM_PROMPT,
            "--output-format",
            "text",
            prompt,
        ]
    raise ValueError("Use --command-template with --harness custom")


def workspace_changes(workspace: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    changes = [line for line in result.stdout.splitlines() if line]
    ignored = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    changes.extend(f"!! {path}" for path in ignored.stdout.splitlines() if path)
    return sorted(set(changes))


def _change_path(change: str) -> str:
    path = change[3:] if len(change) > 3 else change
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[1]
    return path.strip('"')


def unexpected_workspace_changes(workspace: Path) -> list[str]:
    return [
        change
        for change in workspace_changes(workspace)
        if not any(
            _change_path(change).startswith(prefix)
            for prefix in TEMPORARY_OUTPUT_PREFIXES
        )
    ]


def evaluation_output(completed: subprocess.CompletedProcess[str]) -> str:
    """Return only the harness response, excluding diagnostic/tool stderr."""
    return completed.stdout


def evaluate_required_artifacts(
    workspace: Path, requirements: list[dict[str, Any]]
) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    artifact_paths: set[str] = set()
    for requirement in requirements:
        matches = sorted(
            path for path in workspace.glob(requirement["glob"]) if path.is_file()
        )
        artifact_paths.update(path.relative_to(workspace).as_posix() for path in matches)
        minimum = requirement.get("min_matches", 1)
        if len(matches) < minimum:
            failures.append(
                f"artifact glob {requirement['glob']} matched {len(matches)}; expected {minimum}"
            )
            continue
        combined = "\n".join(
            path.read_text(encoding="utf-8", errors="replace") for path in matches
        )
        for pattern in requirement.get("required_content", []):
            if re.search(pattern, combined) is None:
                failures.append(
                    f"artifacts for {requirement['glob']} missing content pattern: {pattern}"
                )
    return failures, sorted(artifact_paths)


def evaluate_case(
    case: dict[str, Any],
    harness: str,
    command_template: str | None,
    timeout: int,
    install_skill: bool = True,
) -> dict[str, Any]:
    temporary, workspace = create_fixture(harness, install_skill=install_skill)
    started_at = datetime.now(timezone.utc)
    variant = "skill" if install_skill else "control"
    try:
        command = build_command(harness, workspace, case["prompt"], command_template)
        completed = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        transcript = "\n".join((completed.stdout, completed.stderr)).strip()
        evaluated_output = evaluation_output(completed)
        failures = []
        phase_pattern = PHASE_PATTERNS[case["expected_phase"]]
        if re.search(phase_pattern, evaluated_output) is None:
            failures.append(
                f"missing expected phase signal {case['expected_phase']}: {phase_pattern}"
            )
        for pattern in case["required_output"]:
            if re.search(pattern, evaluated_output) is None:
                failures.append(f"missing output pattern: {pattern}")
        for pattern in case["forbidden_output"]:
            if re.search(pattern, evaluated_output) is not None:
                failures.append(f"forbidden output pattern: {pattern}")
        artifact_failures, artifacts = evaluate_required_artifacts(
            workspace, case["required_artifacts"]
        )
        failures.extend(artifact_failures)
        changes = workspace_changes(workspace)
        unexpected_changes = unexpected_workspace_changes(workspace)
        if case["forbid_workspace_changes"] and unexpected_changes:
            failures.append(f"workspace changed before gate: {unexpected_changes}")
        if completed.returncode != 0:
            failures.append(f"harness exited {completed.returncode}")
        return {
            "case": case["id"],
            "variant": variant,
            "passed": not failures,
            "failures": failures,
            "duration_seconds": round((datetime.now(timezone.utc) - started_at).total_seconds(), 2),
            "workspace_changes": changes,
            "unexpected_workspace_changes": unexpected_changes,
            "artifacts": artifacts,
            "transcript": transcript,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "case": case["id"],
            "variant": variant,
            "passed": False,
            "failures": [f"harness timed out after {timeout} seconds"],
            "duration_seconds": round((datetime.now(timezone.utc) - started_at).total_seconds(), 2),
            "workspace_changes": workspace_changes(workspace),
            "unexpected_workspace_changes": unexpected_workspace_changes(workspace),
            "artifacts": [],
            "transcript": (error.stdout or "") if isinstance(error.stdout, str) else "",
        }
    finally:
        prompt_path = workspace.parent / f"{workspace.name}-eval-prompt.txt"
        prompt_path.unlink(missing_ok=True)
        temporary.cleanup()


def build_report(
    harness: str,
    comparison_mode: bool,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    skill_results = [result for result in results if result["variant"] == "skill"]
    control_results = [
        result for result in results if result["variant"] == "control"
    ]
    return {
        "schema_version": 2,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "harness": harness,
        "comparison_mode": comparison_mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": all(result["passed"] for result in skill_results),
        "skill_pass_rate": (
            sum(result["passed"] for result in skill_results) / len(skill_results)
            if skill_results
            else 0.0
        ),
        "control_pass_rate": (
            sum(result["passed"] for result in control_results)
            / len(control_results)
            if control_results
            else None
        ),
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--harness", choices=("codex", "claude", "custom"), default="codex"
    )
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--command-template",
        help="Override the harness command; supports {workspace}, {prompt}, and {prompt_file}.",
    )
    parser.add_argument("--list", action="store_true", dest="list_cases")
    parser.add_argument("--validate-cases", action="store_true")
    parser.add_argument(
        "--compare-control",
        action="store_true",
        help="Run each prompt both with and without the installed skill.",
    )
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_cases()
    if args.list_cases:
        for case in cases:
            print(case["id"])
        return 0
    if args.validate_cases:
        print(f"Validated {len(cases)} behavioral eval cases.")
        return 0
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")
    if args.harness == "custom" and not args.command_template:
        raise SystemExit("--harness custom requires --command-template")

    selected_ids = set(args.case_ids or [])
    selected = [case for case in cases if not selected_ids or case["id"] in selected_ids]
    unknown = selected_ids - {case["id"] for case in cases}
    if unknown:
        raise SystemExit(f"Unknown case IDs: {', '.join(sorted(unknown))}")

    results = []
    for run_number in range(1, args.runs + 1):
        for case in selected:
            variants = (True, False) if args.compare_control else (True,)
            for install_skill in variants:
                result = evaluate_case(
                    case,
                    args.harness,
                    args.command_template,
                    args.timeout,
                    install_skill=install_skill,
                )
                result["run"] = run_number
                results.append(result)
                status = "PASS" if result["passed"] else "FAIL"
                print(
                    f"{status} run={run_number} variant={result['variant']} "
                    f"case={case['id']}"
                )

    report = build_report(args.harness, args.compare_control, results)
    skill_results = [result for result in results if result["variant"] == "skill"]
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        for result in skill_results:
            if not result["passed"]:
                print(f"  {result['case']}: {'; '.join(result['failures'])}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
