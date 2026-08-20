#!/usr/bin/env python3
"""Mutation tests for the deterministic workflow lifecycle proof."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from types import ModuleType


MODULE_PATH = Path(__file__).with_name("check-lifecycle-proof.py")
FIXTURE_PATH = MODULE_PATH.parents[1] / "evals" / "deterministic-lifecycle.json"


def load_checker() -> ModuleType:
    if not MODULE_PATH.is_file():
        raise AssertionError(f"Missing lifecycle checker: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("check_lifecycle_proof", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LifecycleProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_checker()
        self.fixture = self.checker.load_fixture(FIXTURE_PATH)

    def mutated(self) -> dict:
        return copy.deepcopy(self.fixture)

    def test_reference_fixture_is_valid(self) -> None:
        self.checker.validate_lifecycle(self.fixture)

    def test_requires_exact_transition_order(self) -> None:
        document = self.mutated()
        document["transitions"][3], document["transitions"][4] = (
            document["transitions"][4],
            document["transitions"][3],
        )

        with self.assertRaisesRegex(AssertionError, "transition order"):
            self.checker.validate_lifecycle(document)

    def test_requires_explicit_spec_approval(self) -> None:
        document = self.mutated()
        document["spec"]["approval"]["explicit"] = False

        with self.assertRaisesRegex(AssertionError, "explicit spec approval"):
            self.checker.validate_lifecycle(document)

    def test_plan_must_match_spec_digest(self) -> None:
        document = self.mutated()
        document["plan"]["source_spec_sha256"] = "f" * 64

        with self.assertRaisesRegex(AssertionError, "plan.*spec digest"):
            self.checker.validate_lifecycle(document)

    def test_green_requires_observed_red(self) -> None:
        document = self.mutated()
        document["tdd"]["cycles"][0]["red"]["observed"] = False

        with self.assertRaisesRegex(AssertionError, "GREEN.*observed RED"):
            self.checker.validate_lifecycle(document)

    def test_browser_requires_functional_evidence(self) -> None:
        document = self.mutated()
        document["browser"]["functional_evidence"] = False

        with self.assertRaisesRegex(AssertionError, "functional browser evidence"):
            self.checker.validate_lifecycle(document)

    def test_browser_requires_three_named_viewports_and_artifacts(self) -> None:
        document = self.mutated()
        document["browser"]["scenarios"][0]["viewports"] = document["browser"][
            "scenarios"
        ][0]["viewports"][:2]

        with self.assertRaisesRegex(AssertionError, "small-mobile.*tablet.*desktop"):
            self.checker.validate_lifecycle(document)

        document = self.mutated()
        document["browser"]["scenarios"][0]["viewports"][0]["artifact"] = ""
        with self.assertRaisesRegex(AssertionError, "browser artifact"):
            self.checker.validate_lifecycle(document)

    def test_verification_and_review_must_match_candidate_head(self) -> None:
        document = self.mutated()
        document["review"]["head"] = "b" * 40

        with self.assertRaisesRegex(AssertionError, "candidate HEAD"):
            self.checker.validate_lifecycle(document)

    def test_cleanup_must_follow_ship_and_remove_temporary_artifacts(self) -> None:
        document = self.mutated()
        document["cleanup"]["after_ship"] = False

        with self.assertRaisesRegex(AssertionError, "cleanup.*ship"):
            self.checker.validate_lifecycle(document)

        document = self.mutated()
        document["cleanup"]["surfaces"]["plan"] = True
        with self.assertRaisesRegex(AssertionError, "temporary artifacts"):
            self.checker.validate_lifecycle(document)

    def test_publication_must_be_draft_at_reviewed_head(self) -> None:
        document = self.mutated()
        document["publication"]["draft"] = False

        with self.assertRaisesRegex(AssertionError, "draft publication"):
            self.checker.validate_lifecycle(document)

    def test_evidence_boundary_cannot_claim_real_harness_execution(self) -> None:
        document = self.mutated()
        document["evidence_boundary"] = "real-harness-execution"
        document["claims_real_harness_execution"] = True

        with self.assertRaisesRegex(
            AssertionError, "deterministic-contract-fixture"
        ):
            self.checker.validate_lifecycle(document)


if __name__ == "__main__":
    unittest.main()
