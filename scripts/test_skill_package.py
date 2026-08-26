#!/usr/bin/env python3
"""End-to-end tests for the reversible skill package installer."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "skill-package.py"
RECEIPT = ".charlies-workflow-skills/receipt.json"


def load_package_module() -> ModuleType:
    scripts_path = str(SCRIPT.parent)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    spec = importlib.util.spec_from_file_location("skill_package", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(self.home)
        return subprocess.run(
            ["python3", str(SCRIPT), *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_success(
        self, result: subprocess.CompletedProcess[str]
    ) -> subprocess.CompletedProcess[str]:
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result

    def test_no_destination_refuses_to_write(self) -> None:
        result = self.run_cli("install", "--skill", "brainstorming")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit destination", result.stderr)
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.home / ".claude").exists())

    def test_project_scope_uses_each_harness_root(self) -> None:
        expectations = {
            "codex": ".agents/skills",
            "cursor": ".agents/skills",
            "claude": ".claude/skills",
        }
        for harness, relative in expectations.items():
            with self.subTest(harness=harness):
                project = self.root / f"project-{harness}"
                project.mkdir()
                result = self.run_cli(
                    "install",
                    "--scope",
                    "project",
                    "--project-dir",
                    str(project),
                    "--harness",
                    harness,
                    "--skill",
                    "brainstorming",
                )

                self.assert_success(result)
                self.assertTrue((project / relative / "brainstorming").is_dir())

    def test_user_scope_uses_agents_or_claude_root(self) -> None:
        for harness, relative in (
            ("codex", ".agents/skills"),
            ("claude", ".claude/skills"),
        ):
            with self.subTest(harness=harness):
                isolated_home = self.root / f"home-{harness}"
                isolated_home.mkdir()
                original_home = self.home
                self.home = isolated_home
                try:
                    result = self.run_cli(
                        "install",
                        "--scope",
                        "user",
                        "--harness",
                        harness,
                        "--skill",
                        "brainstorming",
                    )
                finally:
                    self.home = original_home

                self.assert_success(result)
                self.assertTrue((isolated_home / relative / "brainstorming").is_dir())

    def test_selected_charlie_expands_dependency_closure(self) -> None:
        target = self.root / "selected"
        result = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "charlies-workflow",
        )

        self.assert_success(result)
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        charlie = next(
            skill
            for skill in manifest["skills"]
            if skill["name"] == "charlies-workflow"
        )
        expected = {*charlie["dependencies"]["bundled"], "charlies-workflow"}
        installed = {
            path.name
            for path in target.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        self.assertEqual(installed, expected)

        receipt = json.loads((target / RECEIPT).read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["name"] for entry in receipt["skills"]],
            receipt["resolved_skills"],
        )

    def test_selected_content_workflow_installs_parent_then_child(self) -> None:
        source_child = ROOT / "skills" / "charlies-content-workflow" / "SKILL.md"
        source_parent = ROOT / "skills" / "charlies-workflow" / "SKILL.md"
        source_parent_bytes = source_parent.read_bytes()

        for harness in ("codex", "claude", "cursor"):
            with self.subTest(harness=harness):
                target = self.root / f"content-{harness}"
                result = self.run_cli(
                    "install",
                    "--target-dir",
                    str(target),
                    "--harness",
                    harness,
                    "--skill",
                    "charlies-content-workflow",
                )
                self.assert_success(result)

                receipt = json.loads((target / RECEIPT).read_text(encoding="utf-8"))
                self.assertEqual(
                    receipt["resolved_skills"][-2:],
                    ["charlies-workflow", "charlies-content-workflow"],
                )
                self.assertTrue((target / "charlies-workflow" / "SKILL.md").is_file())
                installed_child = target / "charlies-content-workflow"
                self.assertTrue((installed_child / "SKILL.md").is_file())

                metadata = (installed_child / "agents" / "openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("allow_implicit_invocation: false", metadata)
                child_text = (installed_child / "SKILL.md").read_text(encoding="utf-8")
                if harness == "codex":
                    self.assertNotIn("disable-model-invocation", child_text)
                else:
                    self.assertIn("disable-model-invocation: true", child_text)

        self.assertEqual(source_parent_bytes, source_parent.read_bytes())
        if source_child.is_file():
            self.assertNotIn(
                "disable-model-invocation",
                source_child.read_text(encoding="utf-8"),
            )

    def test_installed_skills_include_package_license_and_provenance(self) -> None:
        target = self.root / "licensed"
        result = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "brainstorming",
        )

        self.assert_success(result)
        installed = target / "brainstorming"
        for source_name, installed_name in (
            ("LICENSE", "PACKAGE_LICENSE.txt"),
            ("THIRD_PARTY_NOTICES.md", "PACKAGE_THIRD_PARTY_NOTICES.md"),
            ("manifest.json", "PACKAGE_MANIFEST.json"),
        ):
            with self.subTest(source=source_name):
                self.assertEqual(
                    (installed / installed_name).read_bytes(),
                    (ROOT / source_name).read_bytes(),
                )

    def test_receipt_records_explicit_scope(self) -> None:
        project = self.root / "scoped-project"
        project.mkdir()

        result = self.run_cli(
            "install",
            "--scope",
            "project",
            "--project-dir",
            str(project),
            "--harness",
            "codex",
            "--skill",
            "brainstorming",
        )

        self.assert_success(result)
        receipt = json.loads(
            (project / ".agents/skills" / RECEIPT).read_text(encoding="utf-8")
        )
        self.assertEqual(receipt["scope"], "project")

    def test_dry_run_creates_nothing(self) -> None:
        target = self.root / "dry-run"
        result = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "brainstorming",
            "--dry-run",
        )

        self.assert_success(result)
        self.assertIn("would install", result.stdout)
        self.assertFalse(target.exists())

    def test_existing_skill_requires_force_and_stays_untouched(self) -> None:
        target = self.root / "existing"
        existing = target / "brainstorming"
        existing.mkdir(parents=True)
        marker = existing / "user.txt"
        marker.write_text("keep me\n", encoding="utf-8")

        result = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "brainstorming",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--force", result.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep me\n")
        self.assertFalse((target / RECEIPT).exists())

    def test_force_backs_up_and_uninstall_restores(self) -> None:
        target = self.root / "replace"
        existing = target / "brainstorming"
        existing.mkdir(parents=True)
        marker = existing / "user.txt"
        marker.write_text("original\n", encoding="utf-8")

        install = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "brainstorming",
            "--force",
        )
        self.assert_success(install)
        self.assertFalse((target / "brainstorming" / "user.txt").exists())

        receipt = json.loads((target / RECEIPT).read_text(encoding="utf-8"))
        entry = next(
            item for item in receipt["skills"] if item["name"] == "brainstorming"
        )
        self.assertEqual(entry["action"], "replaced")
        self.assertRegex(entry["backup_digest"], r"^[0-9a-f]{64}$")
        self.assertTrue((target / entry["backup_path"] / "user.txt").is_file())

        uninstall = self.run_cli("uninstall", "--target-dir", str(target))
        self.assert_success(uninstall)
        self.assertEqual(
            (target / "brainstorming" / "user.txt").read_text(encoding="utf-8"),
            "original\n",
        )
        self.assertFalse((target / RECEIPT).exists())

    def test_force_rejects_symlinked_backup_root(self) -> None:
        target = self.root / "unsafe-backups"
        existing = target / "brainstorming"
        existing.mkdir(parents=True)
        marker = existing / "user.txt"
        marker.write_text("original\n", encoding="utf-8")
        state = target / ".charlies-workflow-skills"
        state.mkdir()
        outside = self.root / "outside-backups"
        outside.mkdir()
        (state / "backups").symlink_to(outside, target_is_directory=True)

        result = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "brainstorming",
            "--force",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("package backups may not be a symlink", result.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), "original\n")
        self.assertEqual(list(outside.iterdir()), [])

    def test_force_restores_preexisting_external_symlink(self) -> None:
        target = self.root / "replace-symlink"
        target.mkdir()
        outside = self.root / "outside-skill"
        outside.mkdir()
        (outside / "user.txt").write_text("original\n", encoding="utf-8")
        destination = target / "brainstorming"
        destination.symlink_to(outside, target_is_directory=True)

        install = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "brainstorming",
            "--force",
        )
        self.assert_success(install)
        self.assertTrue(destination.is_dir())
        self.assertFalse(destination.is_symlink())

        uninstall = self.run_cli("uninstall", "--target-dir", str(target))

        self.assert_success(uninstall)
        self.assertTrue(destination.is_symlink())
        self.assertEqual(destination.readlink(), outside)
        self.assertEqual((destination / "user.txt").read_text(), "original\n")

    def test_uninstall_removes_unchanged_created_skill(self) -> None:
        target = self.root / "created"
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
            )
        )

        uninstall = self.run_cli("uninstall", "--target-dir", str(target))

        self.assert_success(uninstall)
        self.assertFalse((target / "brainstorming").exists())
        self.assertFalse((target / RECEIPT).exists())

    def test_uninstall_retains_locally_modified_skill(self) -> None:
        target = self.root / "modified"
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
            )
        )
        marker = target / "brainstorming" / "local-change.txt"
        marker.write_text("local\n", encoding="utf-8")

        uninstall = self.run_cli("uninstall", "--target-dir", str(target))

        self.assertNotEqual(uninstall.returncode, 0)
        self.assertIn("retained modified", uninstall.stdout)
        self.assertIn("uninstall incomplete", uninstall.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), "local\n")
        receipt = json.loads((target / RECEIPT).read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["name"] for entry in receipt["skills"]], ["brainstorming"]
        )

        marker.unlink()
        retry = self.run_cli("uninstall", "--target-dir", str(target))
        self.assert_success(retry)
        self.assertFalse((target / "brainstorming").exists())
        self.assertFalse((target / RECEIPT).exists())

    def test_modified_replacement_keeps_backup_until_retry(self) -> None:
        target = self.root / "modified-replacement"
        existing = target / "brainstorming"
        existing.mkdir(parents=True)
        original = existing / "user.txt"
        original.write_text("original\n", encoding="utf-8")
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
                "--force",
            )
        )
        local_change = target / "brainstorming" / "local-change.txt"
        local_change.write_text("local\n", encoding="utf-8")

        first = self.run_cli("uninstall", "--target-dir", str(target))

        self.assertNotEqual(first.returncode, 0)
        receipt = json.loads((target / RECEIPT).read_text(encoding="utf-8"))
        backup = target / receipt["skills"][0]["backup_path"]
        self.assertEqual((backup / "user.txt").read_text(encoding="utf-8"), "original\n")

        local_change.unlink()
        retry = self.run_cli("uninstall", "--target-dir", str(target))
        self.assert_success(retry)
        self.assertEqual(original.read_text(encoding="utf-8"), "original\n")
        self.assertFalse((target / RECEIPT).exists())

    def test_interrupted_multi_skill_uninstall_is_retryable(self) -> None:
        package = load_package_module()
        target = self.root / "interrupted-uninstall"
        for name in ("writing-plans", "brainstorming"):
            existing = target / name
            existing.mkdir(parents=True)
            (existing / "user.txt").write_text(
                f"original {name}\n", encoding="utf-8"
            )
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
                "--force",
            )
        )
        arguments = argparse.Namespace(
            target_dir=str(target),
            scope=None,
            project_dir=None,
            harness="codex",
            dry_run=False,
        )
        original_move = package.shutil.move

        def fail_writing_plans_restore(source: str, destination: str) -> str:
            if Path(destination).name == "writing-plans":
                raise OSError("injected restore failure")
            return original_move(source, destination)

        with mock.patch.object(
            package.shutil,
            "move",
            side_effect=fail_writing_plans_restore,
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(OSError, "injected restore failure"):
                    package.uninstall(arguments)

        receipt = json.loads((target / RECEIPT).read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["name"] for entry in receipt["skills"]],
            ["writing-plans"],
        )
        self.assertEqual(
            (target / "brainstorming" / "user.txt").read_text(encoding="utf-8"),
            "original brainstorming\n",
        )

        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(package.uninstall(arguments), 0)
        self.assertEqual(
            (target / "writing-plans" / "user.txt").read_text(encoding="utf-8"),
            "original writing-plans\n",
        )
        self.assertFalse((target / RECEIPT).exists())

    def test_uninstall_recovers_after_restore_before_progress_write(self) -> None:
        package = load_package_module()
        target = self.root / "restore-before-checkpoint"
        for name in ("writing-plans", "brainstorming"):
            existing = target / name
            existing.mkdir(parents=True)
            (existing / "user.txt").write_text(
                f"original {name}\n", encoding="utf-8"
            )
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
                "--force",
            )
        )
        arguments = argparse.Namespace(
            target_dir=str(target),
            scope=None,
            project_dir=None,
            harness="codex",
            dry_run=False,
        )
        receipt_path = target / RECEIPT
        legacy_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for entry in legacy_receipt["skills"]:
            entry.pop("backup_digest", None)
        receipt_path.write_text(json.dumps(legacy_receipt), encoding="utf-8")

        with mock.patch.object(
            package,
            "_write_uninstall_progress",
            side_effect=OSError("injected checkpoint failure"),
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(OSError, "injected checkpoint failure"):
                    package.uninstall(arguments)

        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(len(receipt["skills"]), 2)
        self.assertEqual(
            (target / "brainstorming" / "user.txt").read_text(encoding="utf-8"),
            "original brainstorming\n",
        )

        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(package.uninstall(arguments), 0)
        for name in ("writing-plans", "brainstorming"):
            self.assertEqual(
                (target / name / "user.txt").read_text(encoding="utf-8"),
                f"original {name}\n",
            )
        self.assertFalse((target / RECEIPT).exists())

    def test_legacy_replacement_receipt_without_backup_digest_is_migrated(self) -> None:
        target = self.root / "legacy-receipt"
        existing = target / "brainstorming"
        existing.mkdir(parents=True)
        original = existing / "user.txt"
        original.write_text("original\n", encoding="utf-8")
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
                "--force",
            )
        )
        receipt_path = target / RECEIPT
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for entry in receipt["skills"]:
            entry.pop("backup_digest", None)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        result = self.run_cli("uninstall", "--target-dir", str(target))

        self.assert_success(result)
        self.assertEqual(original.read_text(encoding="utf-8"), "original\n")
        self.assertFalse(receipt_path.exists())

    def test_uninstall_rejects_receipt_skill_path_escape(self) -> None:
        package = load_package_module()
        target = self.root / "unsafe-receipt"
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
            )
        )
        outside = self.root / "outside"
        outside.mkdir()
        marker = outside / "keep.txt"
        marker.write_text("keep\n", encoding="utf-8")
        receipt_path = target / RECEIPT
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["skills"] = [
            {
                "name": "../outside",
                "action": "created",
                "source_digest": "a" * 64,
                "installed_digest": package.tree_digest(outside),
                "backup_path": None,
            }
        ]
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        result = self.run_cli("uninstall", "--target-dir", str(target))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe skill name", result.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_claude_and_cursor_adapt_only_explicit_entries(self) -> None:
        source_charlie = (
            ROOT / "skills" / "charlies-workflow" / "SKILL.md"
        ).read_bytes()
        for harness in ("claude", "cursor"):
            with self.subTest(harness=harness):
                target = self.root / f"adapt-{harness}"
                result = self.run_cli(
                    "install",
                    "--target-dir",
                    str(target),
                    "--harness",
                    harness,
                    "--skill",
                    "charlies-workflow",
                )
                self.assert_success(result)

                explicit = (
                    target / "charlies-workflow" / "SKILL.md"
                ).read_text(encoding="utf-8")
                implicit = (
                    target / "brainstorming" / "SKILL.md"
                ).read_text(encoding="utf-8")
                self.assertIn("disable-model-invocation: true", explicit)
                self.assertNotIn("disable-model-invocation", implicit)

        self.assertEqual(
            (ROOT / "skills" / "charlies-workflow" / "SKILL.md").read_bytes(),
            source_charlie,
        )

    def test_second_install_requires_uninstall_first(self) -> None:
        target = self.root / "active"
        self.assert_success(
            self.run_cli(
                "install",
                "--target-dir",
                str(target),
                "--skill",
                "brainstorming",
            )
        )

        second = self.run_cli(
            "install",
            "--target-dir",
            str(target),
            "--skill",
            "doc-it",
            "--force",
        )

        self.assertNotEqual(second.returncode, 0)
        self.assertIn("uninstall first", second.stderr)
        self.assertFalse((target / "doc-it").exists())

    def test_source_directory_cannot_be_an_install_target(self) -> None:
        package = load_package_module()
        package_root = self.root / "package"
        skills_root = package_root / "skills"
        source = skills_root / "alpha"
        source.mkdir(parents=True)
        source_file = source / "SKILL.md"
        source_file.write_text(
            "---\nname: alpha\ndescription: Alpha skill.\n---\n",
            encoding="utf-8",
        )
        (package_root / "manifest.json").write_text(
            json.dumps(
                {
                    "name": "fixture",
                    "package_version": "1.0.0",
                    "skills": [
                        {
                            "name": "alpha",
                            "activation": {"implicit": True},
                            "dependencies": {"bundled": []},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        arguments = argparse.Namespace(
            target_dir=str(skills_root),
            scope=None,
            project_dir=None,
            harness="codex",
            skill=["alpha"],
            force=True,
            dry_run=False,
        )

        with mock.patch.object(package, "ROOT", package_root), mock.patch.object(
            package, "SKILLS_ROOT", skills_root
        ):
            with self.assertRaisesRegex(package.PackageError, "source package"):
                package.install(arguments)

        self.assertEqual(
            source_file.read_text(encoding="utf-8"),
            "---\nname: alpha\ndescription: Alpha skill.\n---\n",
        )

    def test_install_rejects_unsafe_manifest_skill_name(self) -> None:
        package = load_package_module()
        package_root = self.root / "unsafe-package"
        skills_root = package_root / "skills"
        skills_root.mkdir(parents=True)
        outside_source = package_root / "outside"
        outside_source.mkdir()
        (outside_source / "SKILL.md").write_text(
            "---\nname: outside\ndescription: Outside skill.\n---\n",
            encoding="utf-8",
        )
        (package_root / "manifest.json").write_text(
            json.dumps(
                {
                    "name": "fixture",
                    "package_version": "1.0.0",
                    "skills": [
                        {
                            "name": "../outside",
                            "activation": {"implicit": True},
                            "dependencies": {"bundled": []},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        arguments = argparse.Namespace(
            target_dir=str(self.root / "unsafe-target"),
            scope=None,
            project_dir=None,
            harness="codex",
            skill=["../outside"],
            force=False,
            dry_run=True,
        )

        with mock.patch.object(package, "ROOT", package_root), mock.patch.object(
            package, "SKILLS_ROOT", skills_root
        ):
            with self.assertRaisesRegex(package.PackageError, "unsafe skill name"):
                package.install(arguments)

    def test_partial_failure_restores_a_preexisting_skill(self) -> None:
        package = load_package_module()
        target = self.root / "rollback"
        existing = target / "brainstorming"
        existing.mkdir(parents=True)
        marker = existing / "user.txt"
        marker.write_text("original\n", encoding="utf-8")
        arguments = argparse.Namespace(
            target_dir=str(target),
            scope=None,
            project_dir=None,
            harness="claude",
            skill=["brainstorming"],
            force=True,
            dry_run=False,
        )

        original_adapter = package.adapt_explicit_skill

        def fail_on_brainstorming(
            skill_root: Path, harness: str, implicit: bool
        ) -> None:
            if skill_root.name == "brainstorming":
                raise RuntimeError("injected adaptation failure")
            original_adapter(skill_root, harness, implicit)

        with mock.patch.object(
            package, "adapt_explicit_skill", side_effect=fail_on_brainstorming
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(
                    RuntimeError, "injected adaptation failure"
                ):
                    package.install(arguments)

        self.assertEqual(marker.read_text(encoding="utf-8"), "original\n")
        self.assertFalse((target / "writing-plans").exists())
        self.assertFalse((target / RECEIPT).exists())
        self.assertFalse((target / ".charlies-workflow-skills").exists())


if __name__ == "__main__":
    unittest.main()
