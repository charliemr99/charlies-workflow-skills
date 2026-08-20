#!/usr/bin/env python3
"""Regression tests for workflow contract validation helpers."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("check-workflow-contract.py")
ROOT = MODULE_PATH.parents[1]
SPEC = importlib.util.spec_from_file_location("check_workflow_contract", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


class RequireExplicitOnlyTests(unittest.TestCase):
    def assert_rejected(self, content: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = Path(directory) / "openai.yaml"
            metadata.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(
                AssertionError,
                "invalid or empty YAML structure|implicit invocation must remain disabled",
            ):
                CONTRACT.require_explicit_only(metadata)

    def test_rejects_empty_yaml_with_assertion(self) -> None:
        self.assert_rejected("")

    def test_rejects_null_policy_with_assertion(self) -> None:
        self.assert_rejected("policy:\n")

    def test_accepts_explicit_only_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = Path(directory) / "openai.yaml"
            metadata.write_text(
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
            CONTRACT.require_explicit_only(metadata)


class RequireOrderedTextTests(unittest.TestCase):
    def test_accepts_required_lifecycle_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "action.md"
            path.write_text(
                "review candidate\nship verdict\npromote decisions\ndelete artifacts\npublish\n",
                encoding="utf-8",
            )
            CONTRACT.require_ordered_text(
                path,
                [
                    "review candidate",
                    "ship verdict",
                    "promote decisions",
                    "delete artifacts",
                    "publish",
                ],
            )

    def test_rejects_cleanup_before_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "action.md"
            path.write_text(
                "delete artifacts\nreview candidate\nship verdict\npublish\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssertionError, "out of order"):
                CONTRACT.require_ordered_text(
                    path,
                    ["review candidate", "ship verdict", "delete artifacts", "publish"],
                )

    def test_rejects_reusing_an_overlapping_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "action.md"
            path.write_text("review candidate\nship verdict\n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "out of order"):
                CONTRACT.require_ordered_text(
                    path,
                    ["review candidate", "candidate"],
                )


class AuthoredFileCoverageTests(unittest.TestCase):
    def test_contract_scans_repo_owned_validation_files(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for path_expression in [
            'ROOT / "scripts" / "check-workflow-contract.py"',
            'ROOT / "scripts" / "test_check_workflow_contract.py"',
            'ROOT / "scripts" / "check-lifecycle-proof.py"',
            'ROOT / "scripts" / "test_check_lifecycle_proof.py"',
            'ROOT / "scripts" / "eval-workflow.py"',
            'ROOT / "scripts" / "test_eval_workflow.py"',
            'ROOT / "scripts" / "skill_relationships.py"',
            'ROOT / "scripts" / "check-skill-relationships.py"',
            'ROOT / "scripts" / "test_check_skill_relationships.py"',
            'ROOT / "scripts" / "skill-package.py"',
            'ROOT / "scripts" / "test_skill_package.py"',
            'ROOT / "scripts" / "install.sh"',
            'ROOT / "scripts" / "uninstall.sh"',
            'ROOT / "scripts" / "validate.sh"',
            'ROOT / ".github" / "workflows" / "validate.yml"',
            'ROOT / "scripts" / "vendor" / "openai-skill-creator" / "NOTICE.md"',
            'ROOT / "evals" / "deterministic-lifecycle.json"',
            'ROOT / "docs" / "compatibility.md"',
            'ROOT / "LICENSE"',
        ]:
            self.assertIn(path_expression, source)


class PackageCoherenceTests(unittest.TestCase):
    def test_docs_and_validation_expose_portability_and_reversibility(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        compatibility_path = ROOT / "docs" / "compatibility.md"
        self.assertTrue(compatibility_path.is_file())
        compatibility = compatibility_path.read_text(encoding="utf-8")
        validation = (ROOT / "scripts" / "validate.sh").read_text(encoding="utf-8")
        workflow = (
            ROOT / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        for phrase in [
            "Codex-first, portable by the Agent Skills format",
            "deterministic contract proof",
            "project install",
            "user install",
            "selective install",
            "receipt",
            "uninstall",
        ]:
            self.assertIn(phrase, readme)
        for phrase in [
            "real Codex, Claude Code, and Cursor lifecycle runs are pending",
            "Hallmark network and third-party asset boundary",
        ]:
            self.assertIn(phrase, compatibility)
        self.assertIn("Charlie-authored skill bodies are MIT", license_text)

        for command in [
            "test_check_skill_relationships.py",
            "test_skill_package.py",
            "test_check_lifecycle_proof.py",
            "check-skill-relationships.py",
            "check-lifecycle-proof.py",
            "skills-ref==0.1.1",
            "agentskills validate",
        ]:
            self.assertIn(command, validation)
        for command in [
            "scripts/install.sh",
            "scripts/uninstall.sh",
            "--scope project",
            "--scope user",
        ]:
            self.assertIn(command, workflow)

    def test_charlie_routes_helpers_through_a_portable_loading_contract(self) -> None:
        helper_loading = (
            ROOT
            / "skills"
            / "charlies-workflow"
            / "references"
            / "helper-loading.md"
        )
        self.assertTrue(helper_loading.is_file())
        self.assertIn(
            "bundled sibling",
            helper_loading.read_text(encoding="utf-8"),
        )

    def test_public_bundle_omits_competing_executing_plans_helper(self) -> None:
        self.assertFalse((ROOT / "skills" / "executing-plans").exists())

    def test_adapted_helpers_do_not_bypass_charlie_artifact_ownership(self) -> None:
        brainstorming = (
            ROOT / "skills" / "brainstorming" / "SKILL.md"
        ).read_text(encoding="utf-8")
        writing_plans = (
            ROOT / "skills" / "writing-plans" / "SKILL.md"
        ).read_text(encoding="utf-8")
        subagents = (
            ROOT / "skills" / "subagent-driven-development" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn("docs/superpowers/specs", brainstorming)
        self.assertNotIn("Spec written and committed", brainstorming)
        self.assertNotIn("docs/superpowers/plans", writing_plans)
        self.assertNotIn("superpowers:executing-plans", writing_plans)
        self.assertNotIn("requesting-code-review", subagents)
        self.assertNotIn("finishing-a-development-branch", subagents)

    def test_manifest_declares_relationship_and_activation_metadata(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("schema_version"), 1)
        self.assertRegex(manifest.get("package_version", ""), r"^\d+\.\d+\.\d+$")
        for skill in manifest["skills"]:
            with self.subTest(skill=skill.get("name")):
                self.assertIn("license", skill)
                self.assertIn("adapted", skill)
                self.assertIn("activation", skill)
                self.assertIsInstance(skill["activation"].get("implicit"), bool)
                self.assertIn("dependencies", skill)
                self.assertIn("bundled", skill["dependencies"])
                self.assertIn("external_optional", skill["dependencies"])
                self.assertIn("source", skill)

    def test_source_frontmatter_stays_within_both_validator_schemas(self) -> None:
        for skill_file in sorted((ROOT / "skills").glob("*/SKILL.md")):
            with self.subTest(skill=skill_file.parent.name):
                frontmatter = skill_file.read_text(encoding="utf-8").split(
                    "---", 2
                )[1]
                self.assertNotIn("compatibility:", frontmatter)


if __name__ == "__main__":
    unittest.main()
