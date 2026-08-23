#!/usr/bin/env python3
"""Unit tests for the real cross-harness lifecycle evaluator."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("eval-full-lifecycle.py")
SPEC = importlib.util.spec_from_file_location("eval_full_lifecycle", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVAL)


class EvalFullLifecycleTests(unittest.TestCase):
    def test_scenario_covers_the_four_ordered_checkpoints(self) -> None:
        scenario = EVAL.load_scenario()
        self.assertEqual(
            scenario["evidence_boundary"],
            "real-harness-lifecycle-evaluation",
        )
        self.assertEqual(
            [turn["expected_phase"] for turn in scenario["turns"]],
            [
                "awaiting-discovery-answer",
                "awaiting-spec-approval",
                "plan-ready",
                "published",
            ],
        )
        self.assertIn("URL", " ".join(scenario["acceptance_criteria"]))
        self.assertTrue(scenario["publication"]["draft_only"])

    def test_prompts_use_each_harness_native_explicit_invocation(self) -> None:
        prompt = "{{workflow}} Improve the feedback inbox."
        self.assertEqual(
            EVAL.render_prompt("codex", prompt),
            "$charlies-workflow Improve the feedback inbox.",
        )
        self.assertEqual(
            EVAL.render_prompt("claude", prompt),
            "/charlies-workflow Improve the feedback inbox.",
        )

    def test_codex_commands_preserve_one_session(self) -> None:
        workspace = Path("/tmp/fixture")
        initial = EVAL.build_initial_command(
            "codex",
            workspace,
            "hello",
            session_id=None,
            additional_writable=Path("/tmp/repository/.git"),
        )
        resumed = EVAL.build_resume_command(
            "codex", workspace, "thread-123", "continue"
        )
        self.assertIn("--json", initial)
        self.assertIn("--approve-for-me", initial)
        self.assertNotIn("--full-auto", initial)
        self.assertNotIn("--sandbox", initial)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", initial)
        self.assertIn("/tmp/repository/.git", initial)
        self.assertIn("resume", resumed)
        self.assertIn("thread-123", resumed)
        self.assertNotIn("--color", resumed)
        self.assertNotIn("--add-dir", resumed)
        self.assertNotIn("--approve-for-me", resumed)

    def test_claude_commands_use_stream_json_and_the_fixed_session_id(self) -> None:
        workspace = Path("/tmp/fixture")
        initial = EVAL.build_initial_command(
            "claude", workspace, "hello", session_id="session-123"
        )
        resumed = EVAL.build_resume_command(
            "claude", workspace, "session-123", "continue"
        )
        self.assertIn("stream-json", initial)
        self.assertIn("--append-system-prompt", initial)
        self.assertIn(EVAL.CLAUDE_SKILL_SYSTEM_PROMPT, initial)
        self.assertIn("session-123", initial)
        self.assertIn("--resume", resumed)
        self.assertIn("session-123", resumed)

    def test_extract_codex_session_id_from_jsonl(self) -> None:
        transcript = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "abc-123"}),
                json.dumps({"type": "item.completed", "item": {"type": "message"}}),
            ]
        )
        self.assertEqual(EVAL.extract_codex_session_id(transcript), "abc-123")

    def test_codex_assertions_only_see_agent_messages(self) -> None:
        transcript = "\n".join(
            [
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "aggregated_output": "Workflow phase: published",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "agent_message",
                            "text": "Workflow phase: plan-ready",
                        },
                    }
                ),
            ]
        )
        self.assertEqual(
            EVAL.assistant_output("codex", transcript),
            "Workflow phase: plan-ready",
        )

    def test_claude_assertions_use_the_terminal_result(self) -> None:
        transcript = "\n".join(
            [
                json.dumps(
                    {
                        "type": "user",
                        "message": {"content": "Workflow phase: published"},
                    }
                ),
                json.dumps(
                    {
                        "type": "result",
                        "subtype": "success",
                        "result": "Workflow phase: awaiting-spec-approval",
                    }
                ),
            ]
        )
        self.assertEqual(
            EVAL.assistant_output("claude", transcript),
            "Workflow phase: awaiting-spec-approval",
        )

    def test_find_session_log_uses_the_harness_native_location(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            codex_log = (
                home
                / ".codex"
                / "sessions"
                / "2026"
                / "08"
                / "22"
                / "rollout-abc-123.jsonl"
            )
            claude_log = (
                home / ".claude" / "projects" / "fixture" / "claude-456.jsonl"
            )
            codex_log.parent.mkdir(parents=True)
            claude_log.parent.mkdir(parents=True)
            codex_log.write_text("{}\n", encoding="utf-8")
            claude_log.write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                EVAL.find_session_log("codex", "abc-123", home), codex_log
            )
            self.assertEqual(
                EVAL.find_session_log("claude", "claude-456", home), claude_log
            )

    def test_decant_plan_is_pinned_and_exports_comparable_evidence(self) -> None:
        plan = EVAL.build_decant_plan(
            Path("/tmp/session.jsonl"), Path("/tmp/evidence")
        )
        rendered = "\n".join(" ".join(command) for command in plan.values())
        self.assertIn("@dosu/decant@0.4.0", rendered)
        self.assertIn("sync --path /tmp/session.jsonl", rendered)
        self.assertIn("economics", plan)
        self.assertIn("files", plan)
        self.assertIn("tools", plan)
        self.assertIn("trajectory", plan)
        self.assertIn("session_json", plan)

    def test_harness_environment_disables_shell_profile_identity_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_dir = Path(directory)
            environment = EVAL.harness_environment(
                report_dir, {"PATH": "/usr/bin", "ZDOTDIR": "/old/profile"}
            )
            self.assertEqual(
                environment["ZDOTDIR"],
                str(report_dir / "harness-zdotdir"),
            )
            self.assertTrue((report_dir / "harness-zdotdir").is_dir())
            self.assertEqual(environment["PATH"], "/usr/bin")

    def test_browser_oracle_requires_the_exact_requested_port(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn('"--strictPort"', source)

    def test_temporary_artifact_check_allows_empty_scaffolding_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workflow_dir = Path(directory) / "output" / "workflow"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "empty-run").mkdir()
            self.assertFalse(EVAL.has_temporary_artifacts(workflow_dir))

            state = workflow_dir / "active-run" / "run-state.json"
            state.parent.mkdir()
            state.write_text("{}\n", encoding="utf-8")
            self.assertTrue(EVAL.has_temporary_artifacts(workflow_dir))

    def test_plan_gate_accepts_typographic_viewport_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            run_dir = workspace / "output" / "workflow" / "run"
            run_dir.mkdir(parents=True)
            (run_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (run_dir / "plan.md").write_text(
                "TDD RED/GREEN at 390\u00d7844, 768\u00d71024, and 1440\u00d7900.\n",
                encoding="utf-8",
            )
            failures = EVAL.evaluate_turn(
                {
                    "id": "plan",
                    "expected_phase": "plan-ready",
                    "forbid_source_changes": False,
                },
                "Workflow phase: plan-ready",
                workspace,
                ["checkpoint/spec.md", "checkpoint/plan.md"],
            )
            self.assertEqual(failures, [])

    def test_discovery_gate_requires_the_canonical_run_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            failures = EVAL.evaluate_turn(
                {
                    "id": "discovery",
                    "expected_phase": "awaiting-discovery-answer",
                    "forbid_source_changes": False,
                },
                "Question?\nWorkflow phase: awaiting-discovery-answer",
                workspace,
                [],
            )
            self.assertIn(
                "discovery did not create the canonical run-state.json",
                failures,
            )

            run_state = workspace / "output" / "workflow" / "run" / "run-state.json"
            run_state.parent.mkdir(parents=True)
            run_state.write_text("{}\n", encoding="utf-8")
            failures = EVAL.evaluate_turn(
                {
                    "id": "discovery",
                    "expected_phase": "awaiting-discovery-answer",
                    "forbid_source_changes": False,
                },
                "Question?\nWorkflow phase: awaiting-discovery-answer",
                workspace,
                ["checkpoints/run/run-state.json"],
            )
            self.assertEqual(failures, [])

    def test_medium_grounding_blocks_discovery_until_run_state_exists(self) -> None:
        skill = (EVAL.ROOT / "skills" / "charlies-workflow" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        action = (
            EVAL.ROOT
            / "skills"
            / "charlies-workflow"
            / "actions"
            / "01-ground-and-route.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "Ground and Route has not passed until that file exists",
            " ".join(skill.split()),
        )
        self.assertIn("Do not read `02-discover-and-spec.md`", action)
        self.assertIn("not production source or configuration", action)

    def test_fixture_is_runnable_and_keeps_eval_state_untracked(self) -> None:
        fixture = EVAL.FIXTURE_PATH
        package = json.loads((fixture / "package.json").read_text(encoding="utf-8"))
        for script in ("dev", "test", "lint", "build", "test:e2e"):
            self.assertIn(script, package["scripts"])
        ignored = (fixture / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".agents/", ignored)
        self.assertIn(".claude/", ignored)
        self.assertIn("output/", ignored)
        lint_config = (fixture / "eslint.config.js").read_text(encoding="utf-8")
        self.assertIn('".agents/**"', lint_config)
        self.assertIn('".claude/**"', lint_config)
        source = (fixture / "src" / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("URLSearchParams", source)


if __name__ == "__main__":
    unittest.main()
