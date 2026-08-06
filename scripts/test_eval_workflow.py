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

    def test_source_change_detection_ignores_non_source_files(self) -> None:
        temporary, workspace = EVAL.create_fixture("codex")
        try:
            (workspace / "README.md").write_text("Changed docs.\n", encoding="utf-8")
            self.assertEqual(EVAL.changed_source_paths(workspace), [])
            (workspace / "src" / "app.js").write_text("changed\n", encoding="utf-8")
            self.assertTrue(EVAL.changed_source_paths(workspace))
        finally:
            temporary.cleanup()

    def test_custom_command_template_preserves_prompt_as_one_argument(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow fixture ") as directory:
            command = EVAL.build_command(
                "codex",
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
