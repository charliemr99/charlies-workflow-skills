<p align="center">
  <img src="assets/greenbyte_logo.png" alt="GreenByte Studios logo" width="96">
</p>

# Charlie's Workflow Skills

Reusable Agent Skills for Charlie's end-to-end development workflow.

Created by GreenByte Studios.

This repository vendors the Agent Skills used by GreenByte Studios for
Charlie's development workflow. The bundle centers on `charlies-workflow`,
which supports scoped work in existing products and greenfield MVP delivery,
plus the companion skills it expects so an AI coding agent can plan, implement,
verify, document, and prepare draft PRs without relying on Charlie's local
skill folders.

## What These Skills Are

Agent Skills are folders with a `SKILL.md` file and optional scripts, references, assets, and harness metadata. AI coding agents load them on demand to follow a repeatable workflow instead of making every process decision from scratch.

This package is the workflow skill set GreenByte Studios uses for feature and
new-project delivery:

- `charlies-workflow` is the main orchestrator, with Feature and Project Tracks.
- Its lean action router loads one phase contract at a time, records approval
  state and spec fingerprints, and refuses to publish unreviewed source changes.
- Superpowers-derived skills handle brainstorming, specs, implementation plans, TDD, worktrees, and execution when the task calls for them.
- UI/UX skills support design quality, responsive review, and browser verification.
- Hallmark provides optional visual-direction study, redesign, and anti-slop
  auditing for approved high-expression surfaces.
- Documentation and PR skills help produce final reports and draft PR metadata.

The result is a portable skills bundle you can install into your preferred AI agent harness.

## Included Skills

- `charlies-workflow`
- Companion skills: `emil-design-eng`, `ui-ux-pro-max`, `hallmark`, `doc-it`, `pr-title-and-description`
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

Feature Track example:

```text
$charlies-workflow
Track: feature

Add team invitations to this existing application.
```

Project Track example:

```text
$charlies-workflow
Track: project

Create an MVP for independent consultants to collect client approvals.
```

If the track is omitted, the workflow selects Feature Track for scoped changes
in established repositories and Project Track for a new product or greenfield
MVP. It asks when both remain plausible after inspecting the environment.

Typical expectation:

1. Inspect repository truth, select Feature or Project Track, and classify risk.
2. Resolve build-changing decisions through dynamic discovery instead of a
   fixed question count.
3. Create a proportional spec, obtain explicit approval in the current
   conversation, and fingerprint the approved version.
4. Derive a separate implementation plan from that exact spec. Medium and
   complex work uses `writing-plans`; production edits remain blocked until the
   plan is ready.
5. Implement the plan with focused TDD and invalidate approvals when material
   requirement drift appears.
6. Run final unit, integration, static, build, and functional browser checks.
7. Run **Verify Beyond the Obvious** as a separate UI/UX quality gate inside the
   same browser session. Meaningful UI gets a three-viewport review at small
   mobile, tablet, and desktop, with screenshots or other useful artifacts.
8. Run a targeted `doc-it` documentation gate, updating a canonical section or
   creating a page only when the final behavior needs durable coverage.
9. Run a decision-promotion gate: discard ordinary planning detail, but extract
   non-obvious long-lived decisions into the repository's canonical ADR,
   architecture, or design documentation.
10. Remove temporary workflow artifacts, review the exact candidate HEAD across
    functional, code, and relevancy axes, and iterate until the verdict is
    `ship`.
11. Report decisions and evidence, then prepare a draft PR when GitHub work is
    in scope.

Project Track first approves an MVP Contract and an Architecture and Delivery
Roadmap. It then delivers vertical milestones through Feature Track instead of
turning the whole MVP into one giant spec, plan, or PR.

Temporary specs and implementation plans are execution aids. The workflow defaults to ignored `output/workflow/<feature-or-run-id>/` artifacts for medium and complex work and keeps them out of the final PR. Plans are always deleted; specs are deleted by default after any genuinely durable decisions have been extracted into concise canonical documentation.

### Optional Hallmark Routing

Hallmark is installed with the bundle but is not a default UI dependency.
Charlie's Workflow selects it only for customer-facing greenfield pages,
brand/marketing/editorial work, explicit high-expression redesigns, or
user-approved design-reference study. Operational dashboards, admin tools,
tables, forms, and localized UI fixes continue to use the repository design
system, Emil Design, and UI/UX Pro Max without Hallmark unless the user
explicitly requests it.

Hallmark audits are advisory. Browser behavior, responsive quality,
accessibility, and interaction still require the normal Playwright and UI/UX
verification gates.

## Behavioral Evaluations

The normal validator checks package structure and workflow invariants without
calling a model. An additional opt-in black-box suite probes phase behavior
against a temporary fixture repository: ambiguous discovery must not edit
source, medium work must stop for spec approval, autonomous `no questions`
must still produce a spec and plan, and UI planning must name browser scenarios
plus the three-viewport quality gate.

Validate the case catalog without model usage:

```bash
python3 scripts/eval-workflow.py --validate-cases
python3 scripts/eval-workflow.py --list
```

Run the suite with a locally authenticated harness:

```bash
python3 scripts/eval-workflow.py --harness codex --runs 3 --report /tmp/charlie-codex-eval.json
python3 scripts/eval-workflow.py --harness claude --runs 3 --report /tmp/charlie-claude-eval.json
```

Model evaluations are intentionally excluded from CI because they are metered,
non-deterministic, and require local harness authentication. For another agent,
use `--command-template` with `{workspace}`, `{prompt}`, or `{prompt_file}`.

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
4. For Hallmark, review upstream changes and update the pinned commit before
   replacing the vendored folder.
5. Run `./scripts/validate.sh`.
6. Run `./scripts/install.sh --dry-run` and a temporary install smoke test.

## License

Repo-owned packaging files are MIT licensed. Vendored skills may include third-party material under their own licenses; see `THIRD_PARTY_NOTICES.md` and any `LICENSE` or `NOTICE` files inside the vendored skill folders.
