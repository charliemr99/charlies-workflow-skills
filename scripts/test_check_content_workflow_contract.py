#!/usr/bin/env python3
"""Regression tests for the content workflow contract validator."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("check-content-workflow-contract.py")


def load_contract():
    if not MODULE_PATH.is_file():
        raise AssertionError(f"Missing content workflow checker: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location(
        "check_content_workflow_contract",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRACT = load_contract()


def valid_manifest() -> dict[str, object]:
    return {
        "skills": [
            {
                "name": "charlies-content-workflow",
                "category": "workflow",
                "ownership": "greenbyte-authored",
                "license": "MIT",
                "adapted": False,
                "activation": {"role": "explicit-entry", "implicit": False},
                "dependencies": {
                    "bundled": ["charlies-workflow"],
                    "external_optional": [],
                },
                "source": {
                    "type": "repository-owned",
                    "path": "skills/charlies-content-workflow",
                },
                "required_resources": list(CONTRACT.REQUIRED_REFERENCES),
            }
        ]
    }


def valid_fixture() -> dict[str, object]:
    return {
        "schema_version": 1,
        "evidence_boundary": "deterministic-content-routing-contract",
        "positive_cases": [
            {
                "id": "benchmark-reel-bilingual",
                "request": "Create bilingual benchmark Reels.",
                "required_gates": sorted(CONTRACT.REQUIRED_POSITIVE_GATES),
            }
        ],
        "negative_cases": [
            {
                "id": "caption-rewrite",
                "request": "Rewrite this Instagram caption.",
                "must_not_implicitly_invoke": True,
            }
        ],
    }


class TextContractTests(unittest.TestCase):
    def write(self, content: str) -> Path:
        temporary = tempfile.NamedTemporaryFile(mode="w", delete=False)
        self.addCleanup(Path(temporary.name).unlink, missing_ok=True)
        with temporary:
            temporary.write(content)
        return Path(temporary.name)

    def test_rejects_missing_freshness_gate(self) -> None:
        path = self.write("claim ledger\n")
        with self.assertRaisesRegex(AssertionError, "freshness"):
            CONTRACT.require_text(path, ["claim ledger", "freshness"])

    def test_requires_content_gates_in_order(self) -> None:
        path = self.write("parent handoff\nscope routing\nclaim gate\nfinal QA\n")
        CONTRACT.require_ordered_text(
            path,
            ["parent handoff", "scope routing", "claim gate", "final QA"],
        )

    def test_rejects_out_of_order_content_gates(self) -> None:
        path = self.write("final QA\nparent handoff\nscope routing\nclaim gate\n")
        with self.assertRaisesRegex(AssertionError, "out of order"):
            CONTRACT.require_ordered_text(
                path,
                ["parent handoff", "scope routing", "claim gate", "final QA"],
            )

    def test_rejects_missing_proportional_comparison_guidance(self) -> None:
        path = self.write("comparison bars\n")
        with self.assertRaisesRegex(AssertionError, "proportional comparisons"):
            CONTRACT.require_text(path, ["proportional comparisons"])

    def test_rejects_forced_benchmark_route(self) -> None:
        path = self.write("Every content request must run a benchmark.\n")
        with self.assertRaisesRegex(AssertionError, "optional"):
            CONTRACT.require_optional_routes(path)


class MetadataContractTests(unittest.TestCase):
    def test_rejects_implicit_openai_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "openai.yaml"
            path.write_text(
                "policy:\n  allow_implicit_invocation: true\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssertionError, "implicit invocation"):
                CONTRACT.require_explicit_only(path)

    def test_rejects_metadata_without_literal_skill_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "openai.yaml"
            path.write_text(
                "interface:\n"
                "  display_name: \"Charlie's Content Workflow\"\n"
                "  short_description: \"Evidence-backed short-form content production\"\n"
                "  default_prompt: \"Create an evidence-backed video.\"\n"
                "policy:\n"
                "  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                AssertionError,
                "\\$charlies-content-workflow",
            ):
                CONTRACT.validate_openai_metadata(path)

    def test_rejects_missing_parent_relationship(self) -> None:
        manifest = valid_manifest()
        manifest["skills"][0]["dependencies"]["bundled"] = []
        with self.assertRaisesRegex(AssertionError, "charlies-workflow"):
            CONTRACT.validate_child_manifest(manifest)

    def test_accepts_explicit_child_relationship(self) -> None:
        CONTRACT.validate_child_manifest(valid_manifest())


class FixtureContractTests(unittest.TestCase):
    def test_accepts_benchmark_and_caption_routing_cases(self) -> None:
        CONTRACT.validate_fixture_document(valid_fixture())

    def test_rejects_positive_case_without_freshness(self) -> None:
        fixture = valid_fixture()
        fixture["positive_cases"][0]["required_gates"].remove("freshness")
        with self.assertRaisesRegex(AssertionError, "freshness"):
            CONTRACT.validate_fixture_document(fixture)

    def test_rejects_missing_caption_rewrite_opt_out(self) -> None:
        fixture = valid_fixture()
        fixture["negative_cases"] = []
        with self.assertRaisesRegex(AssertionError, "caption-rewrite"):
            CONTRACT.validate_fixture_document(fixture)


if __name__ == "__main__":
    unittest.main()
