#!/usr/bin/env python3
"""Regression tests for workflow contract validation helpers."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("check-workflow-contract.py")
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
            'ROOT / "scripts" / "eval-workflow.py"',
            'ROOT / "scripts" / "test_eval_workflow.py"',
            'ROOT / "scripts" / "install.sh"',
            'ROOT / "scripts" / "validate.sh"',
            'ROOT / ".github" / "workflows" / "validate.yml"',
            'ROOT / "scripts" / "vendor" / "openai-skill-creator" / "NOTICE.md"',
        ]:
            self.assertIn(path_expression, source)


if __name__ == "__main__":
    unittest.main()
