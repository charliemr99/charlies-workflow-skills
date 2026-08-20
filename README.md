<p align="center">
  <img src="assets/greenbyte_logo.png" alt="GreenByte Studios logo" width="96">
</p>

# Charlie's Workflow Skills

The development skills used by **GreenByte Studios** to take a software request
from discovery through a reviewed draft pull request. The package is
**Codex-first, portable by the Agent Skills format**.

## Workflow

`charlies-workflow` is an explicit-only router:

- **Feature Track** handles a bounded change in an existing product.
- **Project Track** takes a greenfield product or MVP through vertical
  milestones.

Both tracks ground decisions in the repository, shape and approve a
proportional spec, derive a separate implementation plan, execute through TDD,
plan and capture browser evidence when relevant, update durable documentation,
review the exact candidate commit, and open a draft PR by default. Meaningful
UI work includes a three-viewport quality review.

## Included Skills

- Router: `charlies-workflow`
- Discovery and execution: `brainstorming`, `writing-plans`,
  `test-driven-development`, `using-git-worktrees`,
  `subagent-driven-development`
- UI and browser QA: `emil-design-eng`, `ui-ux-pro-max`, `hallmark`,
  `playwright`, `playwright-interactive`
- Documentation and GitHub: `doc-it`, `pr-title-and-description`

`manifest.json` is the source of truth for ownership, licenses, activation,
resources, and dependency closure.

## Install

Clone the package:

```bash
git clone https://github.com/charliemr99/charlies-workflow-skills.git
cd charlies-workflow-skills
```

### Project Install

For a project install, this is the safest default because it keeps the skills
with one repository:

```bash
# Codex or Cursor -> /path/to/project/.agents/skills
./scripts/install.sh --scope project --project-dir /path/to/project \
  --harness codex --skill charlies-workflow

# Claude Code -> /path/to/project/.claude/skills
./scripts/install.sh --scope project --project-dir /path/to/project \
  --harness claude --skill charlies-workflow
```

### User Install

Use an explicit user install to make the workflow available across projects:

```bash
./scripts/install.sh --scope user --harness codex \
  --skill charlies-workflow
```

Codex and Cursor user installs use `~/.agents/skills`; Claude Code uses
`~/.claude/skills`.

### Selective Install

Repeat `--skill` for a selective install. Bundled dependencies are added
automatically:

```bash
./scripts/install.sh --scope project --project-dir /path/to/project \
  --harness cursor --skill hallmark --skill emil-design-eng
```

Use `--target-dir /explicit/skills/path` for a custom destination. Running
without a project, user, or custom destination is rejected. Existing skills are
also rejected unless `--force` is supplied; forced replacements are backed
up.

Every successful install writes a receipt under
`<skills-root>/.charlies-workflow-skills/receipt.json`. A second install at
that destination requires uninstall first.

### Uninstall

Use the same scope, or point directly to the receipted skills root:

```bash
./scripts/uninstall.sh --scope project --project-dir /path/to/project \
  --harness codex

./scripts/uninstall.sh --target-dir /explicit/skills/path
```

Uninstall removes unchanged package copies, restores forced-install backups,
and retains any installed skill that was modified locally. A partial uninstall
returns nonzero and keeps an active receipt so the modified copy can be handled
deliberately and the uninstall retried.

## Use

Invoke the router explicitly and describe the outcome:

```text
$charlies-workflow Add team invitations to this existing application.
```

Override automatic track selection only when needed:

```text
$charlies-workflow
Track: project

Create an MVP for independent consultants to collect client approvals.
```

Interactive work stops for approval of the final spec before planning.
Autonomous work records approval evidence and preserves the same ordered gates
without routine check-ins.

## Optional Integrations

Hallmark is bundled for suitable expressive visual work. **Automatic Ponytail Routing**
can use the separately installed
[Ponytail plugin](https://github.com/DietrichGebert/ponytail) for scoped
simplicity guidance and diff review; `ultra` and repo-wide audit remain
explicit choices.

See [compatibility and evidence boundaries](docs/compatibility.md) for harness
roots, invocation policy, Hallmark network behavior, and current proof status.

## Validate

```bash
uv run --with pyyaml ./scripts/validate.sh
```

Normal validation includes a deterministic contract proof of the complete
lifecycle. It does not call a model. **Behavioral Smoke Evaluations** remain
opt-in:

```bash
python3 scripts/eval-workflow.py --help
# Optional model-driven comparison:
python3 scripts/eval-workflow.py --compare-control
```

## License

GreenByte Studios packaging and Charlie-authored skill bodies are MIT licensed.
Vendored skills keep their original terms. See [LICENSE](LICENSE) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
