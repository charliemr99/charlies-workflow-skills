#!/usr/bin/env python3
"""Validate the deterministic request-to-draft-PR lifecycle fixture."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "evals" / "deterministic-lifecycle.json"
TRANSITIONS = [
    "grounding",
    "discovery",
    "awaiting-spec-approval",
    "planning",
    "implementing",
    "verifying",
    "documenting",
    "reviewing",
    "publishable",
    "published",
]
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
HEAD_PATTERN = re.compile(r"^[0-9a-f]{40}$")
VIEWPORTS = {
    "small-mobile": (390, 844),
    "tablet": (768, 1024),
    "desktop": (1440, 900),
}


def load_fixture(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionError(f"{path}: invalid lifecycle fixture: {error}") from error
    if not isinstance(document, dict):
        raise AssertionError("lifecycle fixture must be an object")
    return document


def require_object(document: dict[str, Any], key: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise AssertionError(f"{key} must be an object")
    return value


def require_nonempty_string(document: dict[str, Any], key: str, label: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{label} must be a non-empty string")
    return value


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
        raise AssertionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def require_artifact_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AssertionError("browser artifact must be a concrete path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "<" in value or ">" in value:
        raise AssertionError(f"browser artifact must be a safe relative path: {value}")
    if not value.startswith("output/"):
        raise AssertionError(f"browser artifact must live under output/: {value}")
    return value


def validate_lifecycle(document: dict[str, Any]) -> None:
    if document.get("schema_version") != 1:
        raise AssertionError("lifecycle schema_version must be 1")
    if document.get("evidence_boundary") != "deterministic-contract-fixture":
        raise AssertionError(
            "evidence_boundary must equal deterministic-contract-fixture"
        )
    if document.get("claims_real_harness_execution") is not False:
        raise AssertionError(
            "deterministic-contract-fixture cannot claim real harness execution"
        )
    if document.get("harness_runs") != []:
        raise AssertionError(
            "deterministic-contract-fixture must contain no harness runs"
        )
    if document.get("transitions") != TRANSITIONS:
        raise AssertionError(
            "transition order must be exactly: " + " -> ".join(TRANSITIONS)
        )

    request = require_object(document, "request")
    require_nonempty_string(request, "id", "request id")
    require_nonempty_string(request, "outcome", "request outcome")

    grounding = require_object(document, "grounding")
    require_nonempty_string(grounding, "repository", "grounding repository")
    for key in ("facts", "affected_surfaces", "constraints"):
        values = grounding.get(key)
        if not isinstance(values, list) or not values or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise AssertionError(f"grounding {key} must contain concrete evidence")

    decision_ledger = require_object(document, "decision_ledger")
    items = decision_ledger.get("items")
    if (
        decision_ledger.get("status") != "decision-complete"
        or decision_ledger.get("open_material_decisions") != []
        or not isinstance(items, list)
        or not items
    ):
        raise AssertionError("decision ledger must be decision-complete")
    for item in items:
        if not isinstance(item, dict) or item.get("status") not in {
            "settled",
            "deferred",
        }:
            raise AssertionError("decision ledger items must be settled or deferred")
        for key in ("topic", "decision", "evidence"):
            require_nonempty_string(item, key, f"decision ledger {key}")

    spec = require_object(document, "spec")
    require_nonempty_string(spec, "path", "spec path")
    spec_digest = require_sha256(spec.get("sha256"), "spec sha256")
    approval = require_object(spec, "approval")
    if (
        spec.get("status") != "approved"
        or approval.get("explicit") is not True
        or not isinstance(approval.get("evidence"), str)
        or not approval["evidence"].strip()
    ):
        raise AssertionError(
            "explicit spec approval with concrete evidence is required"
        )

    plan = require_object(document, "plan")
    require_nonempty_string(plan, "path", "plan path")
    require_sha256(plan.get("sha256"), "plan sha256")
    if plan.get("source_spec_sha256") != spec_digest:
        raise AssertionError("plan must retain the approved spec digest")
    if (
        plan.get("status") != "ready"
        or plan.get("acceptance_criteria_mapped") is not True
        or plan.get("browser_scenarios_planned") is not True
    ):
        raise AssertionError(
            "plan must map acceptance criteria and browser scenarios before implementation"
        )

    tdd = require_object(document, "tdd")
    cycles = tdd.get("cycles")
    if not isinstance(cycles, list) or not cycles:
        raise AssertionError("at least one witnessed TDD cycle is required")
    for cycle in cycles:
        if not isinstance(cycle, dict):
            raise AssertionError("TDD cycle must be an object")
        red = require_object(cycle, "red")
        green = require_object(cycle, "green")
        if green.get("observed") is True and red.get("observed") is not True:
            raise AssertionError("GREEN requires an observed RED result")
        if red.get("result") != "failed-as-expected":
            raise AssertionError("RED must record the expected failure")
        if green.get("observed") is not True or green.get("result") != "passed":
            raise AssertionError("GREEN must be observed and passed")
        require_nonempty_string(red, "command", "RED command")
        require_nonempty_string(green, "command", "GREEN command")

    browser = require_object(document, "browser")
    if browser.get("applies") is not True:
        raise AssertionError("canonical lifecycle browser evidence must apply")
    if browser.get("functional_evidence") is not True:
        raise AssertionError("functional browser evidence is required")
    scenarios = browser.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise AssertionError("at least one browser scenario is required")
    for scenario in scenarios:
        if not isinstance(scenario, dict) or scenario.get("status") != "passed":
            raise AssertionError("browser scenario must have passed")
        steps = scenario.get("steps")
        if not isinstance(steps, list) or not steps or not all(
            isinstance(step, str) and step.strip() for step in steps
        ):
            raise AssertionError("browser scenario needs concrete functional steps")
        viewports = scenario.get("viewports")
        if not isinstance(viewports, list):
            raise AssertionError(
                "browser viewports must include small-mobile, tablet, desktop"
            )
        by_name = {
            viewport.get("name"): viewport
            for viewport in viewports
            if isinstance(viewport, dict)
        }
        if set(by_name) != set(VIEWPORTS):
            raise AssertionError(
                "browser viewports must include small-mobile, tablet, desktop"
            )
        viewport_artifacts: list[str] = []
        for name, (width, height) in VIEWPORTS.items():
            viewport = by_name[name]
            if viewport.get("width") != width or viewport.get("height") != height:
                raise AssertionError(
                    f"{name} viewport must be exactly {width}x{height}"
                )
            viewport_artifacts.append(
                require_artifact_path(viewport.get("artifact"))
            )
        if len(set(viewport_artifacts)) != len(VIEWPORTS):
            raise AssertionError("browser proof requires distinct viewport artifacts")
        artifacts = scenario.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise AssertionError("browser artifact collection may not be empty")
        for artifact in artifacts:
            require_artifact_path(artifact)

    candidate = require_object(document, "candidate")
    head = candidate.get("head")
    if not isinstance(head, str) or not HEAD_PATTERN.fullmatch(head):
        raise AssertionError("candidate HEAD must be a 40-character lowercase SHA")

    verification = require_object(document, "verification")
    review = require_object(document, "review")
    cleanup = require_object(document, "cleanup")
    publication = require_object(document, "publication")
    for label, section in (
        ("verification", verification),
        ("review", review),
        ("cleanup", cleanup),
        ("publication", publication),
    ):
        if section.get("head") != head:
            raise AssertionError(f"{label} must match the exact candidate HEAD")

    if verification.get("status") != "passed":
        raise AssertionError("candidate verification must pass")
    commands = verification.get("commands")
    if not isinstance(commands, list) or not commands:
        raise AssertionError("candidate verification needs concrete commands")

    documentation = require_object(document, "documentation")
    if (
        documentation.get("status") != "complete"
        or documentation.get("decisions_promoted") is not True
    ):
        raise AssertionError("durable documentation decisions must be promoted")

    axes = review.get("axes")
    required_axes = {"functional", "code", "relevancy"}
    if (
        review.get("verdict") != "ship"
        or not isinstance(axes, dict)
        or set(axes) != required_axes
        or any(axes[axis] != "approved" for axis in required_axes)
    ):
        raise AssertionError(
            "review requires functional, code, and relevancy approval with ship verdict"
        )

    if cleanup.get("after_ship") is not True:
        raise AssertionError("cleanup must run only after the ship verdict")
    surfaces = cleanup.get("surfaces")
    expected_surfaces = {"spec", "plan", "run_state", "review_packages"}
    if (
        cleanup.get("temporary_artifacts_absent") is not True
        or not isinstance(surfaces, dict)
        or set(surfaces) != expected_surfaces
        or any(surfaces[surface] is not False for surface in expected_surfaces)
    ):
        raise AssertionError("cleanup must remove all temporary artifacts")

    url = publication.get("url")
    if (
        publication.get("draft") is not True
        or not isinstance(url, str)
        or not url.startswith("https://")
        or "/pull/" not in url
    ):
        raise AssertionError("draft publication with a pull request URL is required")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = load_fixture(args.fixture)
    validate_lifecycle(document)
    head = document["candidate"]["head"]
    scenarios = document["browser"]["scenarios"]
    print(
        "Deterministic lifecycle proof is valid: "
        f"{len(document['transitions'])} transitions, "
        f"{len(document['tdd']['cycles'])} TDD cycle(s), "
        f"{len(scenarios)} browser scenario(s), candidate {head}."
    )
    print(
        "Evidence boundary: deterministic contract fixture; "
        "no real harness, browser, GitHub, or model execution is claimed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
