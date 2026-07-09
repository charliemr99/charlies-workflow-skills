#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$ROOT_DIR/skills"
HARNESS="codex"
TARGET_DIR=""
DRY_RUN=0
FORCE=0

usage() {
  cat <<'USAGE'
Usage: scripts/install.sh [options]

Options:
  --harness codex|codex-agents|claude|cursor
      codex        -> ${CODEX_HOME:-$HOME/.codex}/skills
      codex-agents -> $HOME/.agents/skills
      claude       -> $HOME/.claude/skills
      cursor       -> $HOME/.cursor/skills
  --target-dir PATH
      Override the target skill directory.
  --dry-run
      Print what would be copied without changing files.
  --force
      Replace existing skill directories.
  -h, --help
      Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --harness)
      HARNESS="${2:?Missing value for --harness}"
      shift 2
      ;;
    --target-dir)
      TARGET_DIR="${2:?Missing value for --target-dir}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$TARGET_DIR" ]]; then
  case "$HARNESS" in
    codex)
      TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
      ;;
    codex-agents)
      TARGET_DIR="$HOME/.agents/skills"
      ;;
    claude)
      TARGET_DIR="$HOME/.claude/skills"
      ;;
    cursor)
      TARGET_DIR="$HOME/.cursor/skills"
      ;;
    *)
      echo "Unsupported harness: $HARNESS" >&2
      usage >&2
      exit 2
      ;;
  esac
fi

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Missing source skills directory: $SOURCE_DIR" >&2
  exit 1
fi

echo "Installing skills from: $SOURCE_DIR"
echo "Target directory: $TARGET_DIR"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run: no files will be changed"
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$TARGET_DIR"
fi

for skill_dir in "$SOURCE_DIR"/*; do
  [[ -d "$skill_dir" ]] || continue
  skill_name="$(basename "$skill_dir")"
  dest="$TARGET_DIR/$skill_name"

  if [[ -e "$dest" && "$FORCE" -ne 1 ]]; then
    echo "skip existing: $skill_name"
    continue
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ -e "$dest" && "$FORCE" -eq 1 ]]; then
      echo "would replace: $dest"
    else
      echo "would install: $dest"
    fi
    continue
  fi

  if [[ -e "$dest" ]]; then
    rm -rf "$dest"
  fi
  cp -R "$skill_dir" "$dest"
  echo "installed: $skill_name"
done
