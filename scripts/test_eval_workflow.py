#!/usr/bin/env python3
"""Unit tests for the opt-in workflow evaluation runner."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("eval-workflow.py")
SPEC = importlib.util.spec_from_file_location("eval_workflow", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVAL)


class EvalWorkflowTests(unittest.TestCase):
    def test_catalog_contains_each_required_gate(self) -> None:
        case_ids = {case["id"] for case in EVAL.load_cases()}
        self.assertEqual(
            case_ids,
            {
                "vague-feature-stops-in-discovery",
                "medium-feature-requires-spec-approval",
                "autonomous-medium-still-plans",
                "ui-plan-covers-browser-and-viewports",
            },
        )

    def test_workspace_change_detection_rejects_root_and_source_files(self) -> None:
        temporary, workspace = EVAL.create_fixture("codex")
        try:
            (workspace / "README.md").write_text("Changed docs.\n", encoding="utf-8")
            (workspace / "package.json").write_text("{}\n", encoding="utf-8")
            (workspace / "src" / "app.js").write_text("changed\n", encoding="utf-8")
            changes = EVAL.unexpected_workspace_changes(workspace)
            self.assertTrue(any("README.md" in change for change in changes))
            self.assertTrue(any("package.json" in change for change in changes))
            self.assertTrue(any("src/app.js" in change for change in changes))
        finally:
            temporary.cleanup()

    def test_workspace_change_detection_allows_workflow_artifacts(self) -> None:
        temporary, workspace = EVAL.create_fixture("codex")
        try:
            artifact = workspace / "output" / "workflow" / "run" / "spec.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("# Temporary spec\n", encoding="utf-8")
            self.assertEqual(EVAL.unexpected_workspace_changes(workspace), [])
            self.assertTrue(EVAL.workspace_changes(workspace))
        finally:
            temporary.cleanup()

    def test_workspace_change_detection_rejects_other_ignored_output(self) -> None:
        temporary, workspace = EVAL.create_fixture("codex")
        try:
            artifact = workspace / "output" / "unexpected.txt"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("unexpected\n", encoding="utf-8")
            changes = EVAL.unexpected_workspace_changes(workspace)
            self.assertTrue(any("output/unexpected.txt" in change for change in changes))
        finally:
            temporary.cleanup()

    def test_control_fixture_does_not_install_the_skill(self) -> None:
        temporary, workspace = EVAL.create_fixture("codex", install_skill=False)
        try:
            self.assertFalse(
                (workspace / ".agents" / "skills" / "charlies-workflow").exists()
            )
        finally:
            temporary.cleanup()

    def test_prompt_file_stays_outside_the_fixture(self) -> None:
        temporary, workspace = EVAL.create_fixture("codex")
        try:
            EVAL.build_command("codex", workspace, "hello world", None)
            self.assertFalse((workspace / "eval-prompt.txt").exists())
            self.assertEqual(EVAL.unexpected_workspace_changes(workspace), [])
        finally:
            temporary.cleanup()

    def test_custom_command_template_preserves_prompt_as_one_argument(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow fixture ") as directory:
            command = EVAL.build_command(
                "custom",
                Path(directory),
                "hello world",
                "runner --cwd {workspace} --prompt {prompt}",
            )
            self.assertEqual(
                command,
                ["runner", "--cwd", directory, "--prompt", "hello world"],
            )


if __name__ == "__main__":
    unittest.main()
