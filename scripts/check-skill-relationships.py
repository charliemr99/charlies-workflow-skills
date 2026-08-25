#!/usr/bin/env python3
"""Validate the package manifest, dependency graph, links, and activation."""

from __future__ import annotations

from skill_relationships import ROOT, load_manifest, validate_all


def main() -> None:
    validate_all(ROOT)
    skill_count = len(load_manifest(ROOT)["skills"])
    print(f"Skill relationship graph is valid ({skill_count} bundled skills).")


if __name__ == "__main__":
    main()
