#!/usr/bin/env python3
"""Install and uninstall the bundled skills with receipts and safe rollback."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skill_relationships import load_manifest, resolve_bundled_closure


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
PACKAGE_STATE = ".charlies-workflow-skills"
RECEIPT_NAME = "receipt.json"
HARNESSES = ("codex", "claude", "cursor")
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PACKAGE_DOCUMENTS = {
    "LICENSE": "PACKAGE_LICENSE.txt",
    "THIRD_PARTY_NOTICES.md": "PACKAGE_THIRD_PARTY_NOTICES.md",
    "manifest.json": "PACKAGE_MANIFEST.json",
}


class PackageError(RuntimeError):
    """A user-correctable package operation failure."""


def path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def resolve_target(args: argparse.Namespace, home: Path) -> Path:
    target_value = getattr(args, "target_dir", None)
    scope = getattr(args, "scope", None)
    project_value = getattr(args, "project_dir", None)
    harness = getattr(args, "harness", None)

    if target_value:
        if scope or project_value:
            raise PackageError(
                "--target-dir cannot be combined with --scope or --project-dir"
            )
        return Path(target_value).expanduser().resolve()

    if not scope:
        raise PackageError(
            "an explicit destination is required: use --scope project/user "
            "or --target-dir"
        )
    if not harness:
        raise PackageError("--harness is required with --scope")

    if scope == "project":
        if not project_value:
            raise PackageError("--project-dir is required for project scope")
        base = Path(project_value).expanduser().resolve()
    elif scope == "user":
        if project_value:
            raise PackageError("--project-dir is only valid for project scope")
        base = home.expanduser().resolve()
    else:
        raise PackageError(f"unsupported scope: {scope}")

    relative = Path(".claude/skills") if harness == "claude" else Path(
        ".agents/skills"
    )
    return base / relative


def effective_harness(args: argparse.Namespace) -> str:
    harness = getattr(args, "harness", None)
    return harness or "codex"


def _hash_bytes(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def tree_digest(path: Path) -> str:
    """Hash path names, contents, symlink targets, and executable bits."""
    if not path_exists(path):
        raise PackageError(f"cannot digest missing path: {path}")

    digest = hashlib.sha256()
    items = [path]
    if path.is_dir() and not path.is_symlink():
        items.extend(sorted(path.rglob("*"), key=lambda item: item.as_posix()))

    for item in items:
        relative = "." if item == path else item.relative_to(path).as_posix()
        metadata = item.lstat()
        executable = metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        _hash_bytes(digest, relative.encode("utf-8"))
        _hash_bytes(digest, f"{executable:o}".encode("ascii"))

        if item.is_symlink():
            _hash_bytes(digest, b"symlink")
            _hash_bytes(digest, os.readlink(item).encode("utf-8"))
        elif item.is_dir():
            _hash_bytes(digest, b"directory")
        elif item.is_file():
            _hash_bytes(digest, b"file")
            with item.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    _hash_bytes(digest, chunk)
        else:
            raise PackageError(f"unsupported filesystem entry: {item}")

    return digest.hexdigest()


def adapt_explicit_skill(skill_root: Path, harness: str, implicit: bool) -> None:
    if harness not in {"claude", "cursor"} or implicit:
        return

    skill_file = skill_root / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise PackageError(f"{skill_file}: missing YAML frontmatter")

    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing is None:
        raise PackageError(f"{skill_file}: unterminated YAML frontmatter")

    for index in range(1, closing):
        if lines[index].startswith("disable-model-invocation:"):
            if lines[index].strip() != "disable-model-invocation: true":
                lines[index] = "disable-model-invocation: true\n"
            skill_file.write_text("".join(lines), encoding="utf-8")
            return

    lines.insert(closing, "disable-model-invocation: true\n")
    skill_file.write_text("".join(lines), encoding="utf-8")


def selected_skills(
    manifest: dict[str, Any], requested: list[str] | None
) -> tuple[list[str], list[str]]:
    entries = manifest.get("skills")
    if not isinstance(entries, list):
        raise PackageError("manifest skills must be a list")
    requested_names = requested or [
        entry["name"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    ]
    try:
        resolved = resolve_bundled_closure(manifest, requested_names)
    except AssertionError as error:
        raise PackageError(str(error)) from error
    return requested_names, resolved


def _entry_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        entry["name"]: entry
        for entry in manifest["skills"]
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _safe_state_roots(target: Path) -> tuple[Path, Path]:
    state_root = target / PACKAGE_STATE
    if state_root.is_symlink():
        raise PackageError(f"{state_root}: package state may not be a symlink")
    if path_exists(state_root) and not state_root.is_dir():
        raise PackageError(f"{state_root}: package state must be a directory")

    backups_root = state_root / "backups"
    if backups_root.is_symlink():
        raise PackageError(f"{backups_root}: package backups may not be a symlink")
    if path_exists(backups_root) and not backups_root.is_dir():
        raise PackageError(f"{backups_root}: package backups must be a directory")
    return state_root, backups_root


def _safe_backup_path(target: Path, backup_value: str) -> Path:
    relative = Path(backup_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise PackageError(
            f"receipt backup escapes package state: {backup_value}"
        )
    backup = target / relative
    _state_root, backups_root = _safe_state_roots(target)
    backup_root = backups_root.resolve()
    try:
        backup.parent.resolve().relative_to(backup_root)
    except ValueError as error:
        raise PackageError(
            f"receipt backup escapes package state: {backup_value}"
        ) from error
    return backup


def _safe_skill_path(root: Path, name: str, source: str) -> Path:
    if not SKILL_NAME_PATTERN.fullmatch(name):
        raise PackageError(f"unsafe skill name in {source}: {name!r}")
    return root / name


def _write_json_atomic(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_uninstall_progress(
    receipt_path: Path,
    receipt: dict[str, Any],
    pending_names: set[str],
    status: str,
) -> None:
    pending_receipt = dict(receipt)
    pending = [
        entry
        for entry in receipt["skills"]
        if entry["name"] in pending_names
    ]
    pending_receipt["skills"] = pending
    pending_receipt["resolved_skills"] = [entry["name"] for entry in pending]
    pending_receipt["uninstall_status"] = status
    pending_receipt["uninstall_attempted_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    _write_json_atomic(receipt_path, pending_receipt)


def _add_package_documents(skill_root: Path) -> None:
    for source_name, installed_name in PACKAGE_DOCUMENTS.items():
        source = ROOT / source_name
        destination = skill_root / installed_name
        if not source.is_file():
            raise PackageError(f"missing package document: {source}")
        if path_exists(destination):
            raise PackageError(
                f"{skill_root.name}: reserved package document exists: "
                f"{installed_name}"
            )
        shutil.copy2(source, destination)


def _prune_empty_state_directories(state_root: Path) -> None:
    if not state_root.is_dir() or state_root.is_symlink():
        return
    for directory in sorted(
        (path for path in state_root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass
    try:
        state_root.rmdir()
    except OSError:
        pass


def install(args: argparse.Namespace) -> int:
    home = Path(os.environ.get("HOME", str(Path.home())))
    target = resolve_target(args, home)
    harness = effective_harness(args)
    source_root = SKILLS_ROOT.resolve()
    if target == source_root or source_root in target.parents:
        raise PackageError(
            f"{target}: install target may not be inside the source package skills"
        )
    manifest = load_manifest(ROOT)
    requested, resolved = selected_skills(manifest, args.skill)
    entries = _entry_map(manifest)
    state_root, backups_root = _safe_state_roots(target)
    receipt_path = state_root / RECEIPT_NAME

    if receipt_path.is_file():
        raise PackageError(
            f"{target}: an active package receipt exists; uninstall first"
        )

    operations: list[tuple[str, Path, Path, bool]] = []
    for name in resolved:
        source = _safe_skill_path(SKILLS_ROOT, name, "manifest")
        destination = _safe_skill_path(target, name, "manifest")
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            raise PackageError(f"missing source skill: {source}")
        exists = path_exists(destination)
        if exists and not args.force:
            raise PackageError(
                f"{destination} already exists; rerun with --force or choose "
                "another destination"
            )
        operations.append((name, source, destination, exists))

    print(f"target: {target}")
    print(f"harness: {harness}")
    print(f"resolved skills: {', '.join(resolved)}")
    if args.dry_run:
        for name, _source, destination, exists in operations:
            verb = "would replace" if exists else "would install"
            print(f"{verb}: {name} -> {destination}")
        return 0

    target.mkdir(parents=True, exist_ok=True)
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    backup_root = backups_root / run_id
    records: list[dict[str, Any]] = []
    staging_paths: list[Path] = []
    installed_destinations: list[Path] = []
    moved_backups: list[tuple[Path, Path]] = []

    try:
        for name, source, destination, existed in operations:
            backup: Path | None = None
            if existed:
                backup = backup_root / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(backup))
                moved_backups.append((destination, backup))

            staging_parent = Path(
                tempfile.mkdtemp(prefix=f".{name}.install-", dir=target)
            )
            staging_paths.append(staging_parent)
            staged_skill = staging_parent / name
            shutil.copytree(source, staged_skill, symlinks=True)
            _add_package_documents(staged_skill)
            implicit = entries[name]["activation"]["implicit"]
            adapt_explicit_skill(staged_skill, harness, implicit)
            installed_digest = tree_digest(staged_skill)
            os.replace(staged_skill, destination)
            installed_destinations.append(destination)
            staging_parent.rmdir()
            staging_paths.remove(staging_parent)

            record = {
                "name": name,
                "action": "replaced" if existed else "created",
                "source_digest": tree_digest(source),
                "installed_digest": installed_digest,
                "backup_digest": tree_digest(backup) if backup else None,
                "backup_path": (
                    backup.relative_to(target).as_posix() if backup else None
                ),
            }
            records.append(record)
            print(f"installed: {name}")

        receipt = {
            "schema_version": 1,
            "package": manifest.get("name"),
            "package_version": manifest.get("package_version"),
            "run_id": run_id,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "target_dir": str(target),
            "harness": harness,
            "scope": args.scope or "custom",
            "requested_skills": requested,
            "resolved_skills": resolved,
            "skills": records,
        }
        _write_json_atomic(receipt_path, receipt)
    except Exception:
        for destination in reversed(installed_destinations):
            if path_exists(destination):
                remove_path(destination)
        for destination, backup in reversed(moved_backups):
            if path_exists(destination):
                remove_path(destination)
            if path_exists(backup):
                shutil.move(str(backup), str(destination))
        for staging in staging_paths:
            if path_exists(staging):
                remove_path(staging)
        _prune_empty_state_directories(state_root)
        raise

    print(f"receipt: {receipt_path}")
    return 0


def _load_receipt(target: Path) -> tuple[Path, dict[str, Any]]:
    state_root, _backups_root = _safe_state_roots(target)
    receipt_path = state_root / RECEIPT_NAME
    if not receipt_path.is_file():
        raise PackageError(f"{target}: no active package receipt")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PackageError(f"{receipt_path}: invalid receipt: {error}") from error
    if not isinstance(receipt, dict) or not isinstance(receipt.get("skills"), list):
        raise PackageError(f"{receipt_path}: invalid receipt structure")
    recorded_target = receipt.get("target_dir")
    if recorded_target != str(target):
        raise PackageError(
            f"{receipt_path}: target mismatch ({recorded_target!r} != {str(target)!r})"
        )
    return receipt_path, receipt


def uninstall(args: argparse.Namespace) -> int:
    home = Path(os.environ.get("HOME", str(Path.home())))
    target = resolve_target(args, home)
    receipt_path, receipt = _load_receipt(target)
    classifications: list[tuple[dict[str, Any], str, Path | None]] = []
    seen_names: set[str] = set()

    for raw_entry in reversed(receipt["skills"]):
        if not isinstance(raw_entry, dict) or not isinstance(
            raw_entry.get("name"), str
        ):
            raise PackageError("receipt contains an invalid skill entry")
        name = raw_entry["name"]
        if name in seen_names:
            raise PackageError(f"receipt contains duplicate skill entry: {name}")
        seen_names.add(name)
        destination = _safe_skill_path(target, name, "receipt")
        action = raw_entry.get("action")
        if action not in {"created", "replaced"}:
            raise PackageError(f"{name}: invalid action in receipt")
        for digest_key in ("source_digest", "installed_digest"):
            digest = raw_entry.get(digest_key)
            if not isinstance(digest, str) or not DIGEST_PATTERN.fullmatch(digest):
                raise PackageError(f"{name}: invalid {digest_key} in receipt")
        current_digest: str | None = None
        if path_exists(destination):
            current_digest = tree_digest(destination)
            state = (
                "unchanged"
                if current_digest == raw_entry.get("installed_digest")
                else "modified"
            )
        else:
            state = "missing"

        backup: Path | None = None
        backup_value = raw_entry.get("backup_path")
        backup_digest = raw_entry.get("backup_digest")
        if action == "replaced" and not backup_value:
            raise PackageError(f"{name}: replaced entry requires a backup path")
        if action == "created" and backup_value is not None:
            raise PackageError(f"{name}: created entry may not have a backup path")
        if action == "replaced" and (
            not isinstance(backup_digest, str)
            or not DIGEST_PATTERN.fullmatch(backup_digest)
        ):
            raise PackageError(f"{name}: replaced entry requires a backup digest")
        if action == "created" and backup_digest is not None:
            raise PackageError(f"{name}: created entry may not have a backup digest")
        if backup_value is not None:
            if not isinstance(backup_value, str):
                raise PackageError(f"{name}: invalid backup path in receipt")
            backup = _safe_backup_path(target, backup_value)
            if not path_exists(backup):
                if current_digest == backup_digest:
                    state = "restored"
                else:
                    raise PackageError(f"{name}: required backup is missing: {backup}")
        classifications.append((raw_entry, state, backup))

    for entry, state, _backup in classifications:
        name = entry["name"]
        if state == "restored":
            print(
                f"would retain restored: {name}"
                if args.dry_run
                else f"already restored: {name}"
            )
        elif state == "modified":
            print(f"would retain modified: {name}" if args.dry_run else f"retained modified: {name}")
        elif entry.get("action") == "replaced":
            print(f"would restore: {name}" if args.dry_run else f"restored: {name}")
        else:
            print(f"would remove: {name}" if args.dry_run else f"removed: {name}")
    if args.dry_run:
        return 1 if any(state == "modified" for _, state, _ in classifications) else 0

    retained: list[dict[str, Any]] = []
    pending_names = {entry["name"] for entry, _state, _backup in classifications}
    for entry, state, backup in classifications:
        name = entry["name"]
        destination = _safe_skill_path(target, name, "receipt")
        if state == "restored":
            pending_names.remove(name)
            _write_uninstall_progress(
                receipt_path,
                receipt,
                pending_names,
                "uninstall-in-progress",
            )
            continue
        if state == "modified":
            retained.append(entry)
            _write_uninstall_progress(
                receipt_path,
                receipt,
                pending_names,
                "uninstall-in-progress",
            )
            continue

        if path_exists(destination):
            remove_path(destination)
        if entry.get("action") == "replaced" and backup is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(backup), str(destination))
        pending_names.remove(name)
        _write_uninstall_progress(
            receipt_path,
            receipt,
            pending_names,
            "uninstall-in-progress",
        )

    state_root = target / PACKAGE_STATE
    if retained:
        _write_uninstall_progress(
            receipt_path,
            receipt,
            {entry["name"] for entry in retained},
            "incomplete-modified-skills-retained",
        )
        print(
            "error: uninstall incomplete; locally modified skills remain under "
            "the active receipt",
            file=sys.stderr,
        )
        return 1

    receipt_path.unlink()

    _prune_empty_state_directories(state_root)

    print(f"uninstalled package receipt from: {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install or uninstall Charlie's workflow skill package."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_destination_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--scope", choices=("project", "user"))
        subparser.add_argument("--project-dir")
        subparser.add_argument("--target-dir")
        subparser.add_argument("--harness", choices=HARNESSES)

    install_parser = subparsers.add_parser("install")
    add_destination_arguments(install_parser)
    install_parser.add_argument("--skill", action="append")
    install_parser.add_argument("--force", action="store_true")
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.set_defaults(handler=install)

    uninstall_parser = subparsers.add_parser("uninstall")
    add_destination_arguments(uninstall_parser)
    uninstall_parser.add_argument("--dry-run", action="store_true")
    uninstall_parser.set_defaults(handler=uninstall)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (AssertionError, OSError, PackageError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
