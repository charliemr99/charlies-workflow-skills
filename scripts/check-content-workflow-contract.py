#!/usr/bin/env python3
"""Validate Charlie's content workflow package contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from skill_relationships import validate_all as validate_skill_relationships


ROOT = Path(__file__).resolve().parents[1]
CHILD_NAME = "charlies-content-workflow"
CHILD = ROOT / "skills" / CHILD_NAME
FIXTURE = ROOT / "evals" / "charlies-content-workflow-contract.json"
MAX_ENTRYPOINT_LINES = 180
REQUIRED_REFERENCES = (
    "references/content-brief-and-research.md",
    "references/claims-and-evidence.md",
    "references/production-and-hyperframes.md",
    "references/final-av-qa-and-handoff.md",
)
REQUIRED_POSITIVE_GATES = frozenset(
    {
        "claim-ledger",
        "freshness",
        "benchmark-protocol",
        "shot-matrix",
        "bilingual-timing",
        "compiled-output",
        "caption-face-safety",
        "full-decode",
        "final-claim-reconciliation",
    }
)


def require_text(path: Path, phrases: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    normalized = " ".join(content.split())
    missing = [
        phrase
        for phrase in phrases
        if " ".join(phrase.split()) not in normalized
    ]
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


def require_explicit_only(path: Path) -> None:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    policy = document.get("policy") if isinstance(document, dict) else None
    if (
        not isinstance(policy, dict)
        or policy.get("allow_implicit_invocation") is not False
    ):
        raise AssertionError(f"{path}: implicit invocation must remain disabled")


def require_optional_routes(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    lowered = content.lower()
    forced = [
        phrase
        for phrase in (
            "every content request must run a benchmark",
            "benchmarks are mandatory",
            "hyperframes is required for every",
            "every request requires hyperframes",
        )
        if phrase in lowered
    ]
    if "optional" not in lowered or forced:
        raise AssertionError(
            f"{path}: benchmark and HyperFrames routes must remain optional; "
            f"forced={forced}"
        )


def validate_child_manifest(manifest: dict[str, Any]) -> None:
    entries = manifest.get("skills")
    if not isinstance(entries, list):
        raise AssertionError("manifest: skills must be a list")
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("name") == CHILD_NAME
    ]
    if len(matches) != 1:
        raise AssertionError(f"manifest: expected one {CHILD_NAME} entry")
    child = matches[0]
    expected = {
        "category": "workflow",
        "ownership": "greenbyte-authored",
        "license": "MIT",
        "adapted": False,
        "activation": {"role": "explicit-entry", "implicit": False},
        "source": {
            "type": "repository-owned",
            "path": "skills/charlies-content-workflow",
        },
    }
    for key, value in expected.items():
        if child.get(key) != value:
            raise AssertionError(f"manifest: {CHILD_NAME} has invalid {key}")
    dependencies = child.get("dependencies")
    bundled = dependencies.get("bundled") if isinstance(dependencies, dict) else None
    if bundled != ["charlies-workflow"]:
        raise AssertionError(
            f"manifest: {CHILD_NAME} must bundle charlies-workflow as its parent"
        )
    if dependencies.get("external_optional") != []:
        raise AssertionError(f"manifest: {CHILD_NAME} has unexpected dependencies")
    if child.get("required_resources") != list(REQUIRED_REFERENCES):
        raise AssertionError(f"manifest: {CHILD_NAME} resources are incomplete")


def validate_fixture_document(document: dict[str, Any]) -> None:
    if document.get("schema_version") != 1:
        raise AssertionError("content fixture schema_version must be 1")
    if document.get("evidence_boundary") != "deterministic-content-routing-contract":
        raise AssertionError("content fixture evidence boundary is missing")

    positives = document.get("positive_cases")
    if not isinstance(positives, list):
        raise AssertionError("content fixture positive_cases must be a list")
    positive = next(
        (
            case
            for case in positives
            if isinstance(case, dict) and case.get("id") == "benchmark-reel-bilingual"
        ),
        None,
    )
    if positive is None:
        raise AssertionError("content fixture missing benchmark-reel-bilingual")
    gates = positive.get("required_gates")
    if not isinstance(gates, list) or not all(isinstance(gate, str) for gate in gates):
        raise AssertionError("benchmark-reel-bilingual required_gates are invalid")
    missing_gates = sorted(REQUIRED_POSITIVE_GATES - set(gates))
    if missing_gates:
        raise AssertionError(
            f"benchmark-reel-bilingual missing gates: {missing_gates}"
        )

    negatives = document.get("negative_cases")
    if not isinstance(negatives, list):
        raise AssertionError("content fixture negative_cases must be a list")
    negative = next(
        (
            case
            for case in negatives
            if isinstance(case, dict) and case.get("id") == "caption-rewrite"
        ),
        None,
    )
    if negative is None:
        raise AssertionError("content fixture missing caption-rewrite")
    if negative.get("must_not_implicitly_invoke") is not True:
        raise AssertionError("caption-rewrite must not implicitly invoke the workflow")


def validate_contract(root: Path = ROOT) -> None:
    validate_skill_relationships(root)
    child = root / "skills" / CHILD_NAME
    fixture_path = root / "evals" / "charlies-content-workflow-contract.json"

    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    validate_child_manifest(manifest)
    require_explicit_only(child / "agents" / "openai.yaml")

    lines = (child / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if len(lines) > MAX_ENTRYPOINT_LINES:
        raise AssertionError(
            f"{child / 'SKILL.md'}: entrypoint exceeds {MAX_ENTRYPOINT_LINES} lines"
        )
    if (child / "actions").exists():
        raise AssertionError(f"{child}: child may not duplicate parent action files")

    require_text(
        child / "SKILL.md",
        [
            "$charlies-content-workflow",
            "explicit-only",
            "charlies-workflow",
            "Strategy and research only",
            "Evidence-backed pre-production package",
            "Full production and master delivery",
            "Refresh or re-version",
            "source ledger",
            "claim ledger",
            "shot matrix",
            "compiled masters",
            "publication authority boundary",
            *REQUIRED_REFERENCES,
        ],
    )
    require_ordered_text(
        child / "SKILL.md",
        [
            "## Parent Handoff",
            "## Scope Routing",
            "### 1. Brief and Research Gate",
            "### 2. Claim and Evidence Gate",
            "### 3. Editorial and Production Gate",
            "### 4. Final Master and Handoff Gate",
            "## Authority Boundary",
        ],
    )
    require_optional_routes(child / "SKILL.md")

    require_text(
        child / "references" / "content-brief-and-research.md",
        [
            "one core promise",
            "one CTA",
            "funnel stage",
            "Capture date",
            "Freshness",
            "known, assumed, time-sensitive, deferred, or blocked",
            "primary or authoritative current sources",
        ],
    )
    claims = child / "references" / "claims-and-evidence.md"
    require_text(
        claims,
        [
            "`fact`",
            "`computation`",
            "`benchmark`",
            "`projection`",
            "`opinion`",
            "`blocked`",
            "within 24 hours of final export",
            "public-safe",
            "Real site footage",
            "source repository",
            "machine",
            "routes",
            "commands",
            "runtime",
            "package manager",
            "warmups",
            "measured runs",
            "statistics and ranges",
            "raw logs",
            "benchmark manifest",
            "project-specific scope",
        ],
    )
    require_optional_routes(claims)

    production = child / "references" / "production-and-hyperframes.md"
    require_text(
        production,
        [
            "English and Spanish are separately timed variants",
            "Natural recorded audio becomes the edit master clock",
            "Visual owner",
            "Spoken line",
            "On-screen text",
            "Evidence source",
            "Caveat",
            "Edit instruction",
            "Readiness",
            "framing",
            "eye line",
            "safe areas",
            "alternate takes",
            "handles",
            "room tone",
            "Preserve original recordings",
            "real brand assets",
            "mobile",
            "consistent safe margins",
            "compact layouts",
            "proportional comparisons",
            "deterministic timelines",
            "no more than two",
            "lower-middle",
            "-14 LUFS",
            "<= -1.5 dBTP",
            "final encode",
        ],
    )
    require_optional_routes(production)

    final_qa = child / "references" / "final-av-qa-and-handoff.md"
    require_text(
        final_qa,
        [
            "Final compiled output",
            "Full-decode",
            "ffprobe",
            "frame rate",
            "codecs",
            "integrated loudness",
            "true peak",
            "A/V sync",
            "captions cover all speech",
            "contact sheets",
            "black frames",
            "stale labels",
            "final claim ledger",
            "source evidence",
            "final masters",
            "video-stream identity",
            "English and Spanish masters",
            "Publication Authority Boundary",
        ],
    )

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    validate_fixture_document(fixture)


def main() -> None:
    validate_contract(ROOT)
    print("Content workflow contract is valid.")


if __name__ == "__main__":
    main()
