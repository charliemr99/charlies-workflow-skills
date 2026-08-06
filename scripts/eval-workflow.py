#!/usr/bin/env python3
"""Run opt-in black-box behavioral evaluations for Charlie's Workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "charlies-workflow-cases.json"
SKILL_PATH = ROOT / "skills" / "charlies-workflow"
SOURCE_PATHS = ("src", "tests", "app", "pages", "components", "packages")


def load_cases() -> list[dict[str, Any]]:
    document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ValueError("Unsupported behavioral eval schema")
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Behavioral eval suite has no cases")
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


def create_fixture(harness: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
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

    skill_root = workspace / (".claude/skills" if harness == "claude" else ".agents/skills")
    skill_root.mkdir(parents=True)
    shutil.copytree(SKILL_PATH, skill_root / "charlies-workflow")

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
    prompt_path = workspace / "eval-prompt.txt"
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
            "--output-format",
            "text",
            prompt,
        ]
    raise ValueError("Use --command-template for an unsupported harness")


def changed_source_paths(workspace: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *SOURCE_PATHS],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def evaluate_case(
    case: dict[str, Any],
    harness: str,
    command_template: str | None,
    timeout: int,
) -> dict[str, Any]:
    temporary, workspace = create_fixture(harness)
    started_at = datetime.now(timezone.utc)
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
        failures = []
        for pattern in case["required_output"]:
            if re.search(pattern, transcript) is None:
                failures.append(f"missing output pattern: {pattern}")
        for pattern in case["forbidden_output"]:
            if re.search(pattern, transcript) is not None:
                failures.append(f"forbidden output pattern: {pattern}")
        source_changes = changed_source_paths(workspace)
        if case["forbid_source_changes"] and source_changes:
            failures.append(f"source changed before gate: {source_changes}")
        if completed.returncode != 0:
            failures.append(f"harness exited {completed.returncode}")
        return {
            "case": case["id"],
            "passed": not failures,
            "failures": failures,
            "duration_seconds": round((datetime.now(timezone.utc) - started_at).total_seconds(), 2),
            "source_changes": source_changes,
            "transcript": transcript,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "case": case["id"],
            "passed": False,
            "failures": [f"harness timed out after {timeout} seconds"],
            "duration_seconds": round((datetime.now(timezone.utc) - started_at).total_seconds(), 2),
            "source_changes": changed_source_paths(workspace),
            "transcript": (error.stdout or "") if isinstance(error.stdout, str) else "",
        }
    finally:
        temporary.cleanup()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=("codex", "claude"), default="codex")
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--command-template",
        help="Override the harness command; supports {workspace}, {prompt}, and {prompt_file}.",
    )
    parser.add_argument("--list", action="store_true", dest="list_cases")
    parser.add_argument("--validate-cases", action="store_true")
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

    selected_ids = set(args.case_ids or [])
    selected = [case for case in cases if not selected_ids or case["id"] in selected_ids]
    unknown = selected_ids - {case["id"] for case in cases}
    if unknown:
        raise SystemExit(f"Unknown case IDs: {', '.join(sorted(unknown))}")

    results = []
    for run_number in range(1, args.runs + 1):
        for case in selected:
            result = evaluate_case(case, args.harness, args.command_template, args.timeout)
            result["run"] = run_number
            results.append(result)
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{status} run={run_number} case={case['id']}")

    report = {
        "schema_version": 1,
        "harness": args.harness,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": all(result["passed"] for result in results),
        "results": results,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        for result in results:
            if not result["passed"]:
                print(f"  {result['case']}: {'; '.join(result['failures'])}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
