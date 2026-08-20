#!/usr/bin/env python3
"""Behavioral tests for the bundled skill relationship graph."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


MODULE_PATH = Path(__file__).with_name("skill_relationships.py")


def load_relationships() -> ModuleType:
    if not MODULE_PATH.is_file():
        raise AssertionError(f"Missing relationship module: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("skill_relationships", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def skill_entry(
    name: str,
    *,
    bundled: list[str] | None = None,
    implicit: bool = True,
) -> dict[str, object]:
    return {
        "name": name,
        "category": "test",
        "ownership": "greenbyte-authored",
        "license": "MIT",
        "adapted": False,
        "activation": {
            "role": "routed-helper" if implicit else "explicit-entry",
            "implicit": implicit,
        },
        "dependencies": {
            "bundled": bundled or [],
            "external_optional": [],
        },
        "required_resources": [],
        "source": {"type": "repository-owned"},
    }


class PackageFixture:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "skills").mkdir()
        self.entries: list[dict[str, object]] = []

    def close(self) -> None:
        self.temporary.cleanup()

    def add_skill(
        self,
        name: str,
        *,
        body: str = "# Test Skill\n",
        bundled: list[str] | None = None,
        implicit: bool = True,
        codex_explicit: bool = False,
    ) -> None:
        skill = self.root / "skills" / name
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill {name}.\nlicense: MIT\n---\n\n{body}",
            encoding="utf-8",
        )
        if codex_explicit:
            metadata = skill / "agents"
            metadata.mkdir()
            (metadata / "openai.yaml").write_text(
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
        self.entries.append(
            skill_entry(name, bundled=bundled, implicit=implicit)
        )

    def write_manifest(self) -> None:
        document = {
            "schema_version": 1,
            "name": "test-package",
            "package_version": "1.0.0",
            "skills": self.entries,
        }
        (self.root / "manifest.json").write_text(
            json.dumps(document, indent=2) + "\n",
            encoding="utf-8",
        )


class SkillRelationshipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = PackageFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_manifest_must_match_skill_directories(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha")
        (self.fixture.root / "skills" / "orphan").mkdir()
        (self.fixture.root / "skills" / "orphan" / "SKILL.md").write_text(
            "---\nname: orphan\ndescription: Orphan.\n---\n",
            encoding="utf-8",
        )
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "manifest.*directories"):
            relationships.validate_manifest_graph(self.fixture.root)

    def test_missing_bundled_dependency_is_rejected(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha", bundled=["missing"])
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "missing bundled dependency"):
            relationships.validate_manifest_graph(self.fixture.root)

    def test_dependency_cycle_is_rejected(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha", bundled=["beta"])
        self.fixture.add_skill("beta", bundled=["alpha"])
        self.fixture.write_manifest()

        manifest = relationships.load_manifest(self.fixture.root)
        with self.assertRaisesRegex(AssertionError, "dependency cycle"):
            relationships.resolve_bundled_closure(manifest, ["alpha"])

    def test_missing_relative_markdown_link_is_rejected(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha", body="[Missing](references/nope.md)\n")
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "missing link target"):
            relationships.validate_markdown_links(self.fixture.root)

    def test_relative_link_may_not_escape_skill_root(self) -> None:
        relationships = load_relationships()
        (self.fixture.root / "outside.md").write_text("outside\n", encoding="utf-8")
        self.fixture.add_skill("alpha", body="[Outside](../../outside.md)\n")
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "escapes skill root"):
            relationships.validate_markdown_links(self.fixture.root)

    def test_external_links_are_allowed(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill(
            "alpha",
            body="[Web](https://example.com) [Mail](mailto:test@example.com)\n",
        )
        self.fixture.write_manifest()

        relationships.validate_markdown_links(self.fixture.root)

    def test_explicit_activation_requires_codex_policy(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha", implicit=False)
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "explicit activation.*openai.yaml"):
            relationships.validate_activation_policies(self.fixture.root)

    def test_closure_is_stable_and_dependency_first(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha", bundled=["charlie", "beta"])
        self.fixture.add_skill("beta")
        self.fixture.add_skill("charlie", bundled=["beta"])
        self.fixture.write_manifest()

        manifest = relationships.load_manifest(self.fixture.root)

        self.assertEqual(
            relationships.resolve_bundled_closure(manifest, ["alpha"]),
            ["beta", "charlie", "alpha"],
        )

    def test_machine_local_source_path_is_rejected(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha")
        self.fixture.entries[0]["source"] = {
            "type": "repository-owned",
            "path": "/Users/example/.codex/skills/alpha",
        }
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "machine-local source path"):
            relationships.validate_manifest_graph(self.fixture.root)

    def test_missing_declared_resource_is_rejected(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha")
        self.fixture.entries[0]["required_resources"] = ["scripts/search.py"]
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "required resource"):
            relationships.validate_manifest_graph(self.fixture.root)

    def test_third_party_cannot_claim_repository_owned_source(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha")
        self.fixture.entries[0]["ownership"] = "third-party"
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "repository-owned.*ownership"):
            relationships.validate_manifest_graph(self.fixture.root)

    def test_upstream_source_requires_a_provenance_locator(self) -> None:
        relationships = load_relationships()
        self.fixture.add_skill("alpha")
        self.fixture.entries[0]["ownership"] = "third-party"
        self.fixture.entries[0]["source"] = {"type": "upstream"}
        self.fixture.write_manifest()

        with self.assertRaisesRegex(AssertionError, "upstream source.*repository or package"):
            relationships.validate_manifest_graph(self.fixture.root)


if __name__ == "__main__":
    unittest.main()
