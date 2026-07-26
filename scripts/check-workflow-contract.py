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


def require_explicit_only(path: Path) -> None:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if document.get("policy", {}).get("allow_implicit_invocation") is not False:
        raise AssertionError(f"{path}: implicit invocation must remain disabled")


def main() -> None:
    charlie_lines = (CHARLIE / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if len(charlie_lines) >= 500:
        raise AssertionError("Charlie's SKILL.md must stay under 500 lines")

    require_text(
        CHARLIE / "SKILL.md",
        [
            "Feature Track",
            "Project Track",
            "references/project-track.md",
            "references/hallmark-routing.md",
            "No blocking questions",
            "hallmark",
        ],
    )
    require_text(
        CHARLIE / "references" / "project-track.md",
        [
            "MVP Contract",
            "Architecture and Delivery Roadmap",
            "Milestone Loop",
            "launch-ready",
            "Codex Plan Mode",
        ],
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
        ["Feature Track", "Project Track", "Hallmark"],
    )
    require_text(
        ROOT / "THIRD_PARTY_NOTICES.md",
        ["Hallmark", "Nutlope/hallmark"],
    )

    authored_files = [
        CHARLIE / "SKILL.md",
        CHARLIE / "references" / "project-track.md",
        CHARLIE / "references" / "hallmark-routing.md",
        ROOT / "README.md",
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
