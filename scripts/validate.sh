#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/skills"
PYTHON_BIN="${PYTHON:-python3}"
VALIDATOR="${VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

usage() {
  cat <<'USAGE'
Usage: scripts/validate.sh [options]

Options:
  --skills-dir PATH
      Directory containing skill folders. Defaults to ./skills.
  --validator PATH
      Path to Codex quick_validate.py.
  --python PATH
      Python executable to run the validator.
  -h, --help
      Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skills-dir)
      SKILLS_DIR="${2:?Missing value for --skills-dir}"
      shift 2
      ;;
    --validator)
      VALIDATOR="${2:?Missing value for --validator}"
      shift 2
      ;;
    --python)
      PYTHON_BIN="${2:?Missing value for --python}"
      shift 2
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

if [[ ! -f "$VALIDATOR" ]]; then
  echo "Validator not found: $VALIDATOR" >&2
  echo "Set VALIDATOR=/path/to/quick_validate.py or install Codex skill-creator." >&2
  exit 1
fi

if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "Skills directory not found: $SKILLS_DIR" >&2
  exit 1
fi

for skill_dir in "$SKILLS_DIR"/*; do
  [[ -d "$skill_dir" ]] || continue
  if [[ ! -f "$skill_dir/SKILL.md" ]]; then
    echo "Skipping non-skill directory: $skill_dir"
    continue
  fi
  echo "Validating $(basename "$skill_dir")"
  "$PYTHON_BIN" "$VALIDATOR" "$skill_dir"
done

echo "All bundled skills are valid."
