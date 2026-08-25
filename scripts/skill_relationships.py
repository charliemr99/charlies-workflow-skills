#!/usr/bin/env python3
"""Validate and resolve relationships in the bundled Agent Skills package."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK_PATTERN = re.compile(
    r"(?m)^[ \t]{0,3}\[[^\]]+\]:[ \t]*(<[^>\n]+>|\S+)"
)
PACKAGE_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
EXTERNAL_SCHEMES = {"http", "https", "mailto"}
ACTIVATION_ROLES = {"explicit-entry", "routed-helper", "standalone-helper"}
OWNERSHIP_TYPES = {
    "greenbyte-authored",
    "third-party",
    "third-party-adapted",
    "third-party-derived",
}
SOURCE_TYPES = {
    "repository-owned",
    "upstream",
    "upstream-adapted",
    "upstream-derived",
}


def load_manifest(root: Path = ROOT) -> dict[str, Any]:
    path = root / "manifest.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionError(f"{path}: invalid manifest: {error}") from error
    if not isinstance(document, dict):
        raise AssertionError(f"{path}: manifest must be an object")
    return document


def _skill_entries(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("skills")
    if not isinstance(entries, list):
        raise AssertionError("manifest skills must be a list")
    by_name: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise AssertionError("every manifest skill must be an object with a name")
        name = entry["name"]
        if name in by_name:
            raise AssertionError(f"duplicate manifest skill: {name}")
        by_name[name] = entry
    return by_name


def resolve_bundled_closure(
    manifest: dict[str, Any], requested: Iterable[str]
) -> list[str]:
    by_name = _skill_entries(manifest)
    ordered: list[str] = []
    visited: set[str] = set()
    active: set[str] = set()
    active_path: list[str] = []

    def visit(name: str) -> None:
        if name not in by_name:
            raise AssertionError(f"unknown requested skill: {name}")
        if name in active:
            cycle_start = active_path.index(name)
            cycle = [*active_path[cycle_start:], name]
            raise AssertionError(f"dependency cycle: {' -> '.join(cycle)}")
        if name in visited:
            return

        active.add(name)
        active_path.append(name)
        dependencies = by_name[name].get("dependencies")
        if not isinstance(dependencies, dict):
            raise AssertionError(f"{name}: dependencies must be an object")
        bundled = dependencies.get("bundled")
        if not isinstance(bundled, list) or not all(
            isinstance(dependency, str) for dependency in bundled
        ):
            raise AssertionError(f"{name}: bundled dependencies must be strings")
        for dependency in sorted(bundled):
            if dependency not in by_name:
                raise AssertionError(
                    f"{name}: missing bundled dependency {dependency}"
                )
            visit(dependency)
        active_path.pop()
        active.remove(name)
        visited.add(name)
        ordered.append(name)

    for requested_name in requested:
        visit(requested_name)
    return ordered


def _validate_entry(root: Path, name: str, entry: dict[str, Any]) -> None:
    required_fields = {
        "category",
        "ownership",
        "license",
        "adapted",
        "activation",
        "dependencies",
        "required_resources",
        "source",
    }
    missing = sorted(required_fields - set(entry))
    if missing:
        raise AssertionError(f"{name}: manifest fields missing {missing}")
    if not isinstance(entry["license"], str) or not entry["license"].strip():
        raise AssertionError(f"{name}: license must be a non-empty string")
    if not isinstance(entry["adapted"], bool):
        raise AssertionError(f"{name}: adapted must be a boolean")
    ownership = entry["ownership"]
    if ownership not in OWNERSHIP_TYPES:
        raise AssertionError(f"{name}: invalid ownership")

    activation = entry["activation"]
    if not isinstance(activation, dict):
        raise AssertionError(f"{name}: activation must be an object")
    if activation.get("role") not in ACTIVATION_ROLES:
        raise AssertionError(f"{name}: invalid activation role")
    if not isinstance(activation.get("implicit"), bool):
        raise AssertionError(f"{name}: activation.implicit must be a boolean")
    role = activation["role"]
    implicit = activation["implicit"]
    if role == "explicit-entry" and implicit is not False:
        raise AssertionError(f"{name}: explicit-entry requires implicit false")
    if role == "routed-helper" and implicit is not True:
        raise AssertionError(f"{name}: routed-helper requires implicit true")

    dependencies = entry["dependencies"]
    if not isinstance(dependencies, dict):
        raise AssertionError(f"{name}: dependencies must be an object")
    for key in ("bundled", "external_optional"):
        values = dependencies.get(key)
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise AssertionError(f"{name}: dependencies.{key} must be strings")

    source = entry["source"]
    if not isinstance(source, dict) or source.get("type") not in SOURCE_TYPES:
        raise AssertionError(f"{name}: source must identify its type")
    source_type = source["type"]
    if source_type == "repository-owned" and ownership != "greenbyte-authored":
        raise AssertionError(
            f"{name}: repository-owned source requires greenbyte-authored ownership"
        )
    if source_type != "repository-owned" and ownership == "greenbyte-authored":
        raise AssertionError(
            f"{name}: greenbyte-authored ownership requires repository-owned source"
        )
    ownership_contracts = {
        "third-party": ("upstream", False),
        "third-party-adapted": ("upstream-adapted", True),
        "third-party-derived": ("upstream-derived", True),
    }
    if ownership in ownership_contracts:
        expected_source, expected_adapted = ownership_contracts[ownership]
        if source_type != expected_source or entry["adapted"] is not expected_adapted:
            raise AssertionError(
                f"{name}: ownership {ownership} requires source type "
                f"{expected_source} and adapted={str(expected_adapted).lower()}"
            )
    if source_type.startswith("upstream") and not any(
        isinstance(source.get(locator), str) and source[locator].strip()
        for locator in ("repository", "package")
    ):
        raise AssertionError(
            f"{name}: upstream source requires a repository or package"
        )
    if isinstance(source.get("repository"), str):
        commit = source.get("commit")
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise AssertionError(
                f"{name}: upstream repository requires an immutable commit"
            )
    if isinstance(source.get("package"), str):
        version = source.get("version")
        if not isinstance(version, str) or not version.strip():
            raise AssertionError(
                f"{name}: upstream package requires an immutable version"
            )
    source_path = source.get("path")
    if isinstance(source_path, str) and Path(source_path).is_absolute():
        raise AssertionError(f"{name}: machine-local source path is forbidden")

    resources = entry["required_resources"]
    if not isinstance(resources, list) or not all(
        isinstance(resource, str) and resource for resource in resources
    ):
        raise AssertionError(f"{name}: required_resources must be strings")
    skill_root = root / "skills" / name
    for resource in resources:
        resource_path = (skill_root / resource).resolve()
        try:
            resource_path.relative_to(skill_root.resolve())
        except ValueError as error:
            raise AssertionError(
                f"{name}: required resource escapes skill root: {resource}"
            ) from error
        if not resource_path.is_file():
            raise AssertionError(
                f"{name}: required resource is missing or not a file: {resource}"
            )


def validate_manifest_graph(root: Path = ROOT) -> None:
    manifest = load_manifest(root)
    if manifest.get("schema_version") != 1:
        raise AssertionError("manifest schema_version must be 1")
    package_version = manifest.get("package_version")
    if not isinstance(package_version, str) or not PACKAGE_VERSION_PATTERN.fullmatch(
        package_version
    ):
        raise AssertionError("manifest package_version must be semantic x.y.z")

    by_name = _skill_entries(manifest)
    skills_root = root / "skills"
    skill_directories = {path.name: path for path in skills_root.iterdir() if path.is_dir()}
    missing_skill_files = sorted(
        name
        for name, path in skill_directories.items()
        if not (path / "SKILL.md").is_file()
    )
    if missing_skill_files:
        raise AssertionError(
            f"skill directories missing SKILL.md: {missing_skill_files}"
        )
    directory_names = set(skill_directories)
    manifest_names = set(by_name)
    if manifest_names != directory_names:
        missing = sorted(directory_names - manifest_names)
        extra = sorted(manifest_names - directory_names)
        raise AssertionError(
            "manifest and skill directories differ: "
            f"missing manifest entries={missing}, missing directories={extra}"
        )

    for name, entry in by_name.items():
        _validate_entry(root, name, entry)
        for dependency in entry["dependencies"]["bundled"]:
            if dependency not in by_name:
                raise AssertionError(
                    f"{name}: missing bundled dependency {dependency}"
                )
        resolve_bundled_closure(manifest, [name])


def _link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    elif " " in target:
        target = target.split(" ", 1)[0]
    return unquote(target)


def validate_markdown_links(root: Path = ROOT) -> None:
    skills_root = root / "skills"
    resolved_root = root.resolve()
    for markdown in sorted(root.rglob("*.md")):
        try:
            relative_to_skills = markdown.relative_to(skills_root)
        except ValueError:
            boundary = resolved_root
            boundary_label = "package root"
        else:
            if not relative_to_skills.parts:
                continue
            boundary = (skills_root / relative_to_skills.parts[0]).resolve()
            boundary_label = "skill root"

        content = markdown.read_text(encoding="utf-8")
        matches = [
            *LINK_PATTERN.finditer(content),
            *REFERENCE_LINK_PATTERN.finditer(content),
        ]
        for match in matches:
            target = _link_target(match.group(1))
            if not target or target.startswith("#"):
                continue
            parsed = urlsplit(target)
            if parsed.scheme in EXTERNAL_SCHEMES or target.startswith("//"):
                continue
            relative_path = parsed.path
            if not relative_path:
                continue
            candidate = (markdown.parent / relative_path).resolve()
            try:
                candidate.relative_to(boundary)
            except ValueError as error:
                raise AssertionError(
                    f"{markdown}: link escapes {boundary_label}: {target}"
                ) from error
            if not candidate.exists():
                raise AssertionError(f"{markdown}: missing link target: {target}")


def validate_activation_policies(root: Path = ROOT) -> None:
    try:
        import yaml
    except ModuleNotFoundError as error:
        raise AssertionError(
            "PyYAML is required to validate agents/openai.yaml activation policy"
        ) from error

    manifest = load_manifest(root)
    for name, entry in _skill_entries(manifest).items():
        expected_implicit = entry["activation"]["implicit"]
        metadata_path = root / "skills" / name / "agents" / "openai.yaml"
        document: Any = None
        if metadata_path.is_file():
            document = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        policy = document.get("policy") if isinstance(document, dict) else None
        actual = (
            policy.get("allow_implicit_invocation")
            if isinstance(policy, dict)
            else None
        )
        if expected_implicit is False and actual is not False:
            raise AssertionError(
                f"{name}: explicit activation requires agents/openai.yaml policy"
            )
        if expected_implicit is True and actual is False:
            raise AssertionError(
                f"{name}: routed helper may not disable implicit invocation"
            )


def validate_all(root: Path = ROOT) -> None:
    validate_manifest_graph(root)
    validate_markdown_links(root)
    validate_activation_policies(root)
