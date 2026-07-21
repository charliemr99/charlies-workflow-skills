---
name: charlies-workflow
description: Use when the user explicitly invokes $charlies-workflow for a non-trivial feature, bug fix, refactor, UI change, or PR-ready implementation workflow
---

# Charlies Workflow

## Overview

Run Charlie's preferred delivery workflow with rigor proportional to scope and risk. Inspect the real repository, choose an execution mode with the user, implement with TDD, verify the final diff once, and create a draft PR by default.

This skill is opt-in only. Use it only when the user explicitly invokes `$charlies-workflow`.

## Core Principles

- Scale ceremony, documentation, tests, review, and browser coverage to risk.
- Load the minimum useful skills; never load every possible skill just in case.
- Ask once whether to execute inline or with subagents, unless the user already chose.
- Use subagents for bounded independent work, not as approval ceremonies.
- Maintain one verification ledger and one consolidated final review.
- Treat CI and other external reviewers as asynchronous unless the user asks to wait.

## 1. Select Minimal Skills

After the first repository pass, load only skills that will materially affect the task.

Common routing:

- `brainstorming` / `superpowers:brainstorming`: ambiguous or substantial product, UX, or architecture decisions.
- `writing-plans` / `superpowers:writing-plans`: medium or complex implementation plans.
- `test-driven-development` / `superpowers:test-driven-development`: production behavior changes.
- `using-git-worktrees` / `superpowers:using-git-worktrees`: isolation is requested, the checkout is dirty, or the work is PR-bound.
- `emil-design-eng` and `ui-ux-pro-max`: meaningful UI, responsive, accessibility, animation, or interaction work.
- `playwright-interactive` or `playwright`: browser verification.
- `doc-it`: required near publication when the finished behavior,
  architecture, configuration, or operations need durable documentation.
- `pr-title-and-description`: PR publication.

Do not load a skill merely because it is adjacent. Do not make every subagent reload planning or design skills it does not need.

Use `subagent-driven-development` only when the user chooses subagents and the approved plan is complex enough to contain genuinely independent implementation tasks. Directly coordinate ordinary subagents for smaller scopes.

## 2. Ground in Repo Reality

Before broad questions or edits:

- Read repository instructions and package/test commands.
- Inspect the exact files, routes, components, services, or PR named by the user.
- Run `git status --short --branch` and protect unrelated changes.
- Search for existing patterns, tests, permissions, contracts, and runtime behavior.
- Summarize the intended change, affected surfaces, locked decisions, and risky assumptions.

## 3. Execution Strategy Checkpoint

Classify the task after repository inspection:

| Tier | Typical shape |
| --- | --- |
| Small | One surface or package, clear behavior, low-risk and localized changes |
| Medium | Several related files or states, meaningful UI/API behavior, moderate regression risk |
| Complex | Multiple packages or independent workstreams, high-risk permissions, payments, security, migrations, infrastructure, or rollout |

Then recommend a mode with one sentence of reasoning and ask once:

> This task looks small/medium/complex. I recommend inline/subagents because ___. Do you want inline or subagents?

Do not ask again if the user already selected a mode. Do not reopen the choice unless scope changes materially.

### Inline

Recommend inline for small, tightly coupled, or sequential work where delegation would add coordination cost.

### Subagents

Use between 1 and 4 subagents according to real need and platform capacity:

- 1: bounded research, QA, implementation, or review.
- 2: two independent surfaces or workstreams.
- 3-4: multi-package or genuinely parallel complex work.

Subagent rules:

- Give each agent one concrete deliverable and clear boundaries.
- Never duplicate the same implementation or create reviewers for every small adjustment.
- Respect the platform's concurrency limit; the root agent may consume one slot.
- Require a progress update within 2 minutes. If an agent is silent for 2 minutes, interrupt it and continue inline or reassign the bounded task.
- A known long-running command may continue only when the agent reports what is running before the deadline.

## 4. Scale the Spec and Plan

### Small

Use a short implementation brief in chat covering goal, non-goals, affected
files, tests, and browser smoke when relevant. Do not create repository
spec/plan files unless the user or repository explicitly requires them.

### Medium

Write a compact temporary spec, normally no more than about 150 lines, and a
5-12 step implementation plan. Get approval for the spec. Execute the plan
without a second approval unless it introduces a new product or risk decision.

### Complex

Use full brainstorming, a temporary spec, a separate implementation plan, and
explicit approval gates. Cover architecture, contracts, permissions, failure
modes, rollout, tests, browser scenarios, docs, and PR handling.

For medium and complex work, store workflow artifacts under the repository's
ignored working-artifact location, defaulting to
`output/workflow/<feature-or-run-id>/`. Verify the location is ignored before
writing. These files are execution aids: never stage or commit them, and remove
them when the run is complete.

This location and lifecycle explicitly override defaults in `brainstorming` and
`writing-plans` that would otherwise save or commit files under
`docs/superpowers/`.

User instructions override the tier. If the user explicitly asks for a full spec, planning only, or no documentation, honor that request.

## 5. Implement With Focused TDD

Use TDD for behavior changes:

1. Write the narrow failing test and confirm the expected RED.
2. Make the smallest production change for GREEN.
3. Refactor while staying green.
4. Repeat only for additional behavior or regressions.

During implementation, run narrow RED/GREEN tests. Do not repeatedly run the full package suite after every edit.

For documentation, configuration, or skill changes, use the closest deterministic RED/GREEN validation available. If no realistic test seam exists, document the exception and use the strongest practical validation.

## 6. Verification Ledger

Keep a compact ledger in the working plan or commentary:

| Check | Scope | Commit/HEAD | Result | Invalidated by |
| --- | --- | --- | --- | --- |
| Focused tests | Changed behavior | SHA | pass/fail | Behavior or test changes |
| Typecheck/lint | Affected package/files | SHA | pass/fail | Source or config changes |
| Browser smoke | User-facing final diff | SHA | pass/fail | UI, route, or styling changes |

Rules:

- Reuse valid evidence. Reviewers should not rerun checks merely to reproduce existing proof.
- Rerun a check only when relevant later changes, a rebase, stale environment, missing evidence, or a concrete concern can invalidate it.
- Run one proportional final verification after the final diff is stable.
- After rebasing, rerun focused tests and the affected package typecheck; broaden only if conflicts or upstream changes touched the same contract.

Default final verification:

| Tier | Expected checks |
| --- | --- |
| Small | Focused tests, affected typecheck, changed-file lint when useful, one final smoke for user-facing UI |
| Medium | Focused and relevant package tests, typecheck/lint, planned browser session |
| Complex | Broader package or integration suites, typecheck/lint/build as risk requires, full planned browser or live verification |

Do not hide unrelated baseline failures; report them with evidence.

## 7. Consolidated Review

- Run one consolidated review after implementation and before final verification or publication.
- Use two reviewers only for high-risk work or when the user explicitly requests them. Examples include security, payments, migrations, permissions, destructive operations, and cross-package public contracts.
- Reviewers inspect the diff, requirements, and verification ledger first. They run extra commands only for missing, stale, or suspicious evidence.
- If review finds an issue, the implementer fixes it, runs the affected checks, and the original reviewer rechecks that finding. Do not restart the entire spec-review-quality-review-browser chain.
- Do not create a separate review round for formatting, copy, tokens, or other minor adjustments.

## 8. One Final Browser Session

Combine functional and visual QA into one browser session after the final UI diff is stable.

- Small localized UI: test the main path at one representative viewport plus any specifically affected breakpoint.
- Medium or complex responsive UI: normally test small mobile, tablet, and desktop.
- Cover relevant routing, loading/error/empty states, keyboard/focus, accessibility basics, light/dark mode, motion and reduced motion, console errors, and overflow.
- Save only useful screenshots, videos, traces, or logs under the repository artifact convention.
- Do not run a second responsive review that repeats the same scenarios.

If browser QA is skipped, state why the change has no meaningful user-facing surface or why the environment blocked it.

## 9. Documentation and Artifact Lifecycle

Before final review or publication, clean the current run's temporary
spec/plan files. Do not delete unrelated historical artifacts during an
ordinary feature run.

The final diff against the intended PR base must contain no added, modified,
renamed, or copied files under `docs/superpowers/plans/` or
`docs/superpowers/specs/`. Deletions are allowed only for an explicitly scoped
cleanup task. Restore a pre-existing artifact to its base version instead of
deleting it; remove artifacts newly created by the current run.

Check both committed and uncommitted changes; any output blocks publication:

```sh
BASE_REF=origin/main # replace when the intended PR base differs
git log --format= --name-only --diff-filter=AMCR "$BASE_REF"..HEAD -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR "$BASE_REF"...HEAD -- \
  docs/superpowers/plans docs/superpowers/specs
git diff --name-only --diff-filter=AMCR --cached -- \
  docs/superpowers/plans docs/superpowers/specs
git diff --name-only --diff-filter=AMCR -- \
  docs/superpowers/plans docs/superpowers/specs
git ls-files --others --exclude-standard -- \
  docs/superpowers/plans docs/superpowers/specs
git ls-files -- output/workflow
```

Run all commands again after staging and immediately before commit or
push. Do not use `git add .` or another broad staging command after the gate.

Then make an explicit durable-documentation decision:

- Small: documentation is optional when code, tests, and the PR fully explain
  the change.
- Medium: use `doc-it` when behavior, configuration, support, or operations
  would otherwise be difficult to discover.
- Complex: use `doc-it` against the final code and tests to create or update
  concise canonical documentation unless the user explicitly declines or an
  existing canonical page already covers the change.

Permanent documentation describes the feature as it exists: purpose, current
behavior, contracts, configuration, operational or rollout requirements,
troubleshooting, limitations, and verification where relevant. Exclude skill
lists, approval history, task checklists, TDD transcripts, commit choreography,
and PR/Gemini instructions.

The final report should lead with the outcome and include only relevant items:
files/behavior changed, important decisions, final tests, browser artifacts,
skipped checks or baseline failures, canonical documentation links, and PR
status. Never link temporary specs or plans.

## 10. Draft PR and External Checks

Create a draft PR by default after the final verification unless the user opts out.

- Re-check status and stage only intended paths.
- Run the workflow-artifact diff gate from Section 9 before staging and again
  after staging; remove any current-run spec/plan pollution before commit or
  push.
- Use conventional commits and `pr-title-and-description`.
- Verify `gh auth status` and `gh api user --jq .login` before push/PR actions.
- Preserve the worktree after creating a PR.

CI, deployment checks, and automated reviewers are asynchronous by default:

- Query current state once after publication.
- Report queued, pending, unavailable, failed, or complete checks accurately.
- Do not block the task waiting for external systems unless the user explicitly asks to wait, babysit, merge, or resolve all feedback.

## Quality Gates

All tiers require:

- Repo grounding and protected unrelated changes.
- An explicit execution-mode choice or an already stated user preference.
- Scope and acceptance criteria proportional to the tier.
- Temporary workflow artifacts stayed ignored/untracked and were removed at the
  end of the run.
- The final PR diff contains no added, modified, renamed, or copied
  `docs/superpowers` plan/spec artifacts.
- No commit in the PR branch history added or modified workflow artifacts, even
  if a later commit deleted them.
- Durable documentation was explicitly created, updated, confirmed sufficient,
  or deemed unnecessary according to Section 9.
- TDD or a documented approved exception.
- One consolidated review when review is useful.
- One final proportional verification after the final diff.
- Honest reporting and a draft PR attempt unless opted out or blocked.

Medium and complex work additionally require proportional temporary spec/plan
artifacts during execution, not in the final PR. Meaningful UI work requires
the proportional final browser session. Pending external checks do not prevent
workflow completion when reported accurately.

## Common Failure Modes

| Failure | Correction |
| --- | --- |
| Loading every related skill | Load only skills that materially affect the task |
| Using subagent-driven development for a small task | Coordinate directly or work inline |
| Requiring full spec/plan for a localized change | Use the small implementation brief |
| Committing plans/specs because nested skills suggest it | Override their location with ignored `output/workflow/` and remove the files before publication |
| Committing an artifact and deleting it later | Remove it from branch history; final-tree cleanup alone is insufficient |
| Deleting every historical artifact during each run | Clean only the current run; use a separately scoped cleanup task for repository history |
| Replacing a long plan with another long permanent doc | Run targeted `doc-it` and document only current durable behavior and operations |
| Running full tests after every edit | Use narrow RED/GREEN and the verification ledger |
| Reviewer repeats all verification | Reuse evidence; run only missing or suspect checks |
| Reviewing after every adjustment | Run one consolidated review and targeted rechecks |
| Separate functional and visual browser passes | Use one final combined browser session |
| Waiting indefinitely for CI or reviewers | Report pending state unless explicitly asked to monitor |
| Final report becomes a second spec | Lead with outcome and link only canonical documentation |
