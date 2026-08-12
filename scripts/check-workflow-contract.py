#!/usr/bin/env python3
"""Validate the package-level Charlie workflow contract."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHARLIE = ROOT / "skills" / "charlies-workflow"
HALLMARK = ROOT / "skills" / "hallmark"


def require_text(path: Path, phrases: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    missing = [phrase for phrase in phrases if phrase not in content]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")


def require_absent(path: Path, phrases: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    present = [phrase for phrase in phrases if phrase in content]
    if present:
        raise AssertionError(f"{path}: forbidden {present}")


def require_ordered_text(path: Path, phrases: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    cursor = 0
    for phrase in phrases:
        position = content.find(phrase, cursor)
        if position < 0:
            if phrase in content:
                raise AssertionError(f"{path}: phrase out of order {phrase!r}")
            raise AssertionError(f"{path}: missing ordered phrase {phrase!r}")
        cursor = position + len(phrase)


def require_action_contract(path: Path) -> None:
    require_text(
        path,
        ["## Input", "## Output", "## Process", "## Exit Test"],
    )


def require_explicit_only(path: Path) -> None:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise AssertionError(f"{path}: invalid or empty YAML structure")
    policy = document.get("policy")
    if (
        not isinstance(policy, dict)
        or policy.get("allow_implicit_invocation") is not False
    ):
        raise AssertionError(f"{path}: implicit invocation must remain disabled")


def main() -> None:
    charlie_lines = (CHARLIE / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if len(charlie_lines) > 220:
        raise AssertionError("Charlie's SKILL.md must stay at or below 220 lines")

    require_text(
        CHARLIE / "SKILL.md",
        [
            "Feature Track",
            "Project Track",
            "references/project-track.md",
            "references/hallmark-routing.md",
            "references/ponytail-routing.md",
            "No blocking questions",
            "hallmark",
            "ponytail",
            "ponytail-review",
            "ponytail-audit",
            "actions/01-ground-and-route.md",
            "actions/02-discover-and-spec.md",
            "actions/03-plan.md",
            "actions/04-implement.md",
            "actions/05-verify-and-document.md",
            "actions/06-review-and-publish.md",
            "Read only the current action",
        ],
    )
    require_absent(CHARLIE / "SKILL.md", ["Codex Plan Mode"])

    actions = [
        "01-ground-and-route.md",
        "02-discover-and-spec.md",
        "03-plan.md",
        "04-implement.md",
        "05-verify-and-document.md",
        "06-review-and-publish.md",
    ]
    for action in actions:
        require_action_contract(CHARLIE / "actions" / action)

    require_text(
        CHARLIE / "actions" / "01-ground-and-route.md",
        [
            "ponytail_routing",
            "ponytail_mode",
            "automatic",
            "ultra",
            "Do not ask a separate Ponytail mode question",
            "references/ponytail-routing.md",
        ],
    )
    require_text(
        CHARLIE / "actions" / "02-discover-and-spec.md",
        [
            "settled",
            "open",
            "deferred",
            "spec_sha256",
            "spec_approval_evidence",
            "explicit user approval",
            "Every interactive Small brief",
            "complete Small request",
            "explicit execution instruction",
            "No blocking questions",
            "blocker",
            "major",
            "Ponytail",
        ],
    )
    require_text(
        CHARLIE / "actions" / "03-plan.md",
        [
            "writing-plans",
            "approved spec",
            "plan_source_spec_sha256",
            "acceptance criterion",
            "browser scenario",
            "production edits remain blocked",
            "simplicity proof",
        ],
    )
    require_text(
        CHARLIE / "actions" / "04-implement.md",
        [
            "Ponytail",
            "smallest complete behavior",
            "acceptance criteria",
        ],
    )
    require_text(
        CHARLIE / "actions" / "05-verify-and-document.md",
        [
            "Verify Beyond the Obvious",
            "small mobile",
            "tablet",
            "desktop",
            "emil-design-eng",
            "ui-ux-pro-max",
            "references/documentation-and-artifacts.md",
            "Retain",
            "Pre-review Artifact Safety Gate",
        ],
    )
    require_absent(
        CHARLIE / "actions" / "05-verify-and-document.md",
        ["Delete the implementation plan", "Temporary workflow artifacts are absent"],
    )
    require_text(
        CHARLIE / "references" / "documentation-and-artifacts.md",
        [
            "Durable Documentation Gate",
            "Decision Promotion Gate",
            "Pre-review Artifact Safety Gate",
            "Post-ship Artifact Cleanup Gate",
            "git log --format= --name-only --diff-filter=AMCR",
            "git check-ignore -q",
            "Decision promotion: none",
            "Remaining gaps",
        ],
    )
    require_text(
        CHARLIE / "actions" / "06-review-and-publish.md",
        [
            "functional",
            "code",
            "relevancy",
            "ship",
            "iterate",
            "reviewed_head",
            "unreviewed source changes",
            "expected GitHub account",
            "organization-owned repository",
            "gh api user --jq .login",
            "retained through review",
            "ponytail-review",
            "simplicity_review_status",
        ],
    )
    require_ordered_text(
        CHARLIE / "actions" / "06-review-and-publish.md",
        [
            "### 1. Review Candidate",
            "### 2. Ship Verdict",
            "### 3. Decision Promotion",
            "### 4. Artifact Cleanup",
            "### 5. GitHub Identity",
            "### 6. Publish and Report",
        ],
    )
    state = json.loads(
        (CHARLIE / "assets" / "run-state-template.json").read_text(
            encoding="utf-8"
        )
    )
    required_state_keys = {
        "track",
        "tier",
        "approval_mode",
        "phase",
        "spec_status",
        "spec_sha256",
        "spec_approval_evidence",
        "plan_status",
        "plan_source_spec_sha256",
        "verification_head",
        "reviewed_head",
        "review_verdict",
        "documentation_status",
        "ponytail_routing",
        "ponytail_mode",
        "ponytail_reason",
        "simplicity_review_status",
    }
    missing_state_keys = sorted(required_state_keys - set(state))
    if missing_state_keys:
        raise AssertionError(
            f"run-state-template.json: missing {missing_state_keys}"
        )
    expected_state_defaults = {
        "ponytail_routing": "auto",
        "ponytail_mode": "unselected",
        "ponytail_reason": None,
        "simplicity_review_status": "pending",
    }
    invalid_state_defaults = {
        key: state.get(key)
        for key, expected in expected_state_defaults.items()
        if state.get(key) != expected
    }
    if invalid_state_defaults:
        raise AssertionError(
            "run-state-template.json: invalid Ponytail defaults "
            f"{invalid_state_defaults}"
        )
    require_text(
        CHARLIE / "references" / "project-track.md",
        [
            "MVP Contract",
            "Architecture and Delivery Roadmap",
            "Milestone Loop",
            "launch-ready",
            "Product Framing",
            "Decision Spike",
        ],
    )
    require_absent(
        CHARLIE / "references" / "project-track.md", ["Codex Plan Mode"]
    )
    require_text(
        CHARLIE / "references" / "hallmark-routing.md",
        [
            "hallmark study",
            "hallmark redesign",
            "hallmark audit",
            "Normally skip Hallmark",
            "Do not commit `.hallmark/`",
        ],
    )
    require_text(
        CHARLIE / "references" / "ponytail-routing.md",
        [
            "Automatic Selection",
            "lite",
            "full",
            "Never select `ultra` automatically",
            "Do not ask a separate Ponytail mode question",
            "exact mode",
            "ponytail-review",
            "Ponytail Audit Boundary",
            "ponytail-audit",
            "repo-wide",
            "unavailable",
            "security",
            "accessibility",
        ],
    )
    require_explicit_only(CHARLIE / "agents" / "openai.yaml")
    require_explicit_only(HALLMARK / "agents" / "openai.yaml")

    if not (HALLMARK / "LICENSE.txt").is_file():
        raise AssertionError("Vendored Hallmark license is missing")
    require_text(
        HALLMARK / "NOTICE.txt",
        [
            "Nutlope/hallmark",
            "aeb42fb354ff4efa36ab475773a082315a3af2ce",
            "metadata.version",
        ],
    )

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    hallmark = next(
        (skill for skill in manifest["skills"] if skill["name"] == "hallmark"),
        None,
    )
    if hallmark is None:
        raise AssertionError("manifest.json does not list Hallmark")
    if hallmark.get("upstream_commit") != "aeb42fb354ff4efa36ab475773a082315a3af2ce":
        raise AssertionError("manifest.json does not pin the reviewed Hallmark commit")

    require_text(
        ROOT / "README.md",
        [
            "Feature Track",
            "Project Track",
            "Hallmark",
            "Automatic Ponytail Routing",
            "Ponytail plugin",
            "Behavioral Smoke Evaluations",
            "three-viewport",
            "--compare-control",
        ],
    )
    require_text(
        ROOT / "THIRD_PARTY_NOTICES.md",
        ["Hallmark", "Nutlope/hallmark"],
    )

    eval_cases = json.loads(
        (ROOT / "evals" / "charlies-workflow-cases.json").read_text(
            encoding="utf-8"
        )
    )
    if eval_cases.get("schema_version") != 2:
        raise AssertionError("Behavioral eval schema_version must be 2")
    cases = eval_cases.get("cases")
    if not isinstance(cases, list) or len(cases) < 5:
        raise AssertionError("At least five behavioral eval cases are required")
    required_case_keys = {
        "id",
        "prompt",
        "required_output",
        "forbidden_output",
        "expected_phase",
        "forbid_workspace_changes",
        "required_artifacts",
    }
    for case in cases:
        if not isinstance(case, dict) or not required_case_keys.issubset(case):
            raise AssertionError("Behavioral eval case has an invalid shape")
    required_case_ids = {
        "vague-feature-stops-in-discovery",
        "medium-feature-requires-spec-approval",
        "autonomous-medium-still-plans",
        "ui-plan-covers-browser-and-viewports",
        "automatic-ponytail-routing",
    }
    case_ids = {case["id"] for case in cases}
    if not required_case_ids.issubset(case_ids):
        raise AssertionError("Behavioral eval suite is missing a required gate case")
    require_text(
        ROOT / "scripts" / "eval-workflow.py",
        [
            "codex",
            "claude",
            "custom",
            "command-template",
            "forbid_workspace_changes",
            "unexpected_workspace_changes",
            "compare-control",
        ],
    )

    authored_files = [
        CHARLIE / "SKILL.md",
        *(CHARLIE / "actions" / action for action in actions),
        CHARLIE / "assets" / "run-state-template.json",
        CHARLIE / "references" / "project-track.md",
        CHARLIE / "references" / "hallmark-routing.md",
        CHARLIE / "references" / "ponytail-routing.md",
        CHARLIE / "references" / "documentation-and-artifacts.md",
        CHARLIE / "agents" / "openai.yaml",
        ROOT / "README.md",
        ROOT / "evals" / "charlies-workflow-cases.json",
        ROOT / "scripts" / "check-workflow-contract.py",
        ROOT / "scripts" / "test_check_workflow_contract.py",
        ROOT / "scripts" / "eval-workflow.py",
        ROOT / "scripts" / "test_eval_workflow.py",
        ROOT / "scripts" / "install.sh",
        ROOT / "scripts" / "validate.sh",
        ROOT / ".github" / "workflows" / "validate.yml",
        ROOT / "scripts" / "vendor" / "openai-skill-creator" / "NOTICE.md",
        ROOT / "manifest.json",
        ROOT / "THIRD_PARTY_NOTICES.md",
    ]
    placeholders = [
        str(path)
        for path in authored_files
        if "TO" "DO" in path.read_text(encoding="utf-8")
    ]
    if placeholders:
        raise AssertionError(f"Task placeholders found in {placeholders}")

    print("Workflow contract is valid.")


if __name__ == "__main__":
    main()
