<p align="center">
  <img src="assets/greenbyte_logo.png" alt="GreenByte Studios logo" width="96">
</p>

# Charlie's Workflow Skills

The Agent Skills used by GreenByte Studios to plan, implement, verify, and
publish software changes. The bundle works with Codex, Claude Code, Cursor, and
other harnesses that support the Agent Skills format.

## What It Does

`charlies-workflow` is an explicit-only delivery router with two tracks:

- **Feature Track** for changes to an existing product.
- **Project Track** for a greenfield product or MVP delivered in vertical
  milestones.

The workflow grounds itself in the repository, resolves open product decisions,
gets approval for a proportional spec, derives a separate implementation plan,
uses TDD, verifies relevant browser behavior, updates durable documentation,
reviews the exact candidate commit, and opens a draft PR by default.

Meaningful UI work includes a separate three-viewport quality review. Optional
Hallmark routing supports expressive visual work. Automatic Ponytail Routing
selects simplicity guidance when the task would benefit from reuse, native
features, fewer dependencies, or less abstraction.

## Included Skills

- Workflow: `charlies-workflow`
- Planning and delivery: `brainstorming`, `writing-plans`,
  `test-driven-development`, `using-git-worktrees`, `executing-plans`,
  `subagent-driven-development`
- UI and browser QA: `emil-design-eng`, `ui-ux-pro-max`, `hallmark`,
  `playwright`, `playwright-interactive`
- Documentation and GitHub: `doc-it`, `pr-title-and-description`

## Install

```bash
git clone https://github.com/charliemr99/charlies-workflow-skills.git
cd charlies-workflow-skills
```

Choose your harness:

```bash
# Codex: ${CODEX_HOME:-$HOME/.codex}/skills
./scripts/install.sh --harness codex

# Claude Code: $HOME/.claude/skills
./scripts/install.sh --harness claude

# Cursor: $HOME/.cursor/skills
./scripts/install.sh --harness cursor
```

Existing skill folders are preserved. Use `--force` to replace them, or
`--target-dir /path/to/project/.agents/skills` for a project-scoped install.

## Use

Invoke the workflow and describe the outcome. You do not need to repeat its
planning, TDD, browser QA, documentation, or draft-PR instructions.

```text
$charlies-workflow Add team invitations to this existing application.
```

Specify a track only when you want to override automatic routing:

```text
$charlies-workflow
Track: project

Create an MVP for independent consultants to collect client approvals.
```

The workflow asks for spec approval before implementation planning unless you
explicitly request autonomous execution. Autonomous execution preserves the
same planning and quality gates.

### Optional Integrations

- **Hallmark** is bundled and selected only for appropriate visual work.
- **Ponytail** is not bundled. Install the
  [Ponytail plugin](https://github.com/DietrichGebert/ponytail) to enable
  automatic `lite` or `full` simplicity guidance and diff review. `ultra`
  remains explicit, and repo-wide audits do not expand normal feature scope.

## Validate

```bash
uv run --with pyyaml ./scripts/validate.sh
./scripts/install.sh --dry-run
```

Behavioral Smoke Evaluations are optional and never call a model during normal
validation. Run `python3 scripts/eval-workflow.py --help` for local harness
options, including `--compare-control`.

## License

GreenByte Studios packaging files are MIT licensed. Vendored skills retain
their original licenses and notices in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
