<p align="center">
  <img src="assets/greenbyte_logo.png" alt="GreenByte Studios logo" width="96">
</p>

# Charlie's Workflow Skills

Reusable Agent Skills for Charlie's end-to-end development workflow.

Created by GreenByte Studios.

This repository vendors the Agent Skills used by GreenByte Studios for Charlie's development workflow. The bundle centers on `charlies-workflow`, plus the companion skills it expects so an AI coding agent can plan, ask questions, write a spec, create an implementation plan, use TDD, verify in browser when relevant, document the work, and prepare draft PRs without relying on Charlie's local skill folders.

## What These Skills Are

Agent Skills are folders with a `SKILL.md` file and optional scripts, references, assets, and harness metadata. AI coding agents load them on demand to follow a repeatable workflow instead of making every process decision from scratch.

This package is the workflow skill set GreenByte Studios uses for feature work:

- `charlies-workflow` is the main orchestrator.
- Superpowers-derived skills handle brainstorming, specs, implementation plans, TDD, worktrees, and execution.
- UI/UX skills support design quality, responsive review, and browser verification.
- Documentation and PR skills help produce final reports and draft PR metadata.

The result is a portable skills bundle you can install into your preferred AI agent harness.

## Included Skills

- `charlies-workflow`
- Companion skills: `emil-design-eng`, `ui-ux-pro-max`, `doc-it`, `pr-title-and-description`
- Browser skills: `playwright`, `playwright-interactive`
- Vendored Superpowers skills: `brainstorming`, `writing-plans`, `test-driven-development`, `using-git-worktrees`, `executing-plans`, `subagent-driven-development`

`charlies-workflow` is explicit-only in Codex through `skills/charlies-workflow/agents/openai.yaml`.

## Install in Your Preferred Harness

Clone the repo:

```bash
git clone https://github.com/charliemr99/charlies-workflow-skills.git
cd charlies-workflow-skills
```

Dry-run first:

```bash
./scripts/install.sh --dry-run
```

Install globally for a supported harness:

```bash
# Codex personal skills, matching Charlie's current setup
./scripts/install.sh --harness codex

# Claude Code personal skills
./scripts/install.sh --harness claude

# Cursor personal skills
./scripts/install.sh --harness cursor
```

Alternative Codex user scope:

```bash
# Codex official user-scope location
./scripts/install.sh --harness codex-agents
```

Project-scoped installs are also supported:

```bash
# Codex repo-scoped skills
./scripts/install.sh --target-dir /path/to/project/.agents/skills

# Claude Code repo-scoped skills
./scripts/install.sh --target-dir /path/to/project/.claude/skills

# Cursor repo-scoped skills
./scripts/install.sh --target-dir /path/to/project/.cursor/skills
```

By default, existing skill folders are preserved. To replace existing copies:

```bash
./scripts/install.sh --harness codex --force
```

Harness notes:

- Codex supports skills as folders with `SKILL.md`; current Codex docs list repo-scoped `.agents/skills` and user-scoped `$HOME/.agents/skills`, while this package defaults `--harness codex` to `${CODEX_HOME:-$HOME/.codex}/skills` to match Charlie's current Codex setup. Use `--target-dir "$HOME/.agents/skills"` if you prefer the official user scope.
- Claude Code supports personal `~/.claude/skills/` and project `.claude/skills/`.
- Cursor supports Agent Skills; use `~/.cursor/skills/` for personal installs when enabled in your Cursor setup, or `.cursor/skills/` for project-scoped installs.

Restart the agent or reload its skill registry if a newly installed skill does not appear.

## Usage

Invoke explicitly:

```text
$charlies-workflow Please plan and implement this feature end to end.
```

Typical expectation:

1. Inspect repo context.
2. Brainstorm and ask feature-specific questions.
3. Produce a Superpowers-style spec.
4. Wait for spec approval.
5. Create an implementation plan from the approved spec.
6. Implement with TDD.
7. Verify with automated and browser checks when relevant.
8. Run responsive UI/UX review for UI changes.
9. Report results and prepare a draft PR when GitHub work is in scope.

## Validate

The validator uses Codex's official skill validator. It expects PyYAML to be available to the Python interpreter running the validator.

```bash
./scripts/validate.sh
```

If PyYAML is missing:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install PyYAML
./scripts/validate.sh --python python
```

You can validate a temporary install too:

```bash
tmp="$(mktemp -d)"
CODEX_HOME="$tmp/codex" ./scripts/install.sh --harness codex
./scripts/validate.sh --skills-dir "$tmp/codex/skills"
```

## Update Process

1. Refresh source skills locally.
2. Copy updated skill folders into `skills/`.
3. Update `manifest.json` and `THIRD_PARTY_NOTICES.md` when upstream versions, sources, or licenses change.
4. Run `./scripts/validate.sh`.
5. Run `./scripts/install.sh --dry-run` and a temporary install smoke test.

## License

Repo-owned packaging files are MIT licensed. Vendored skills may include third-party material under their own licenses; see `THIRD_PARTY_NOTICES.md` and any `LICENSE` or `NOTICE` files inside the vendored skill folders.
