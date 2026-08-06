---
name: charlies-workflow
description: Use when the user explicitly invokes $charlies-workflow for a greenfield project, MVP, feature, bug fix, refactor, UI change, or PR-ready implementation workflow
---

# Charlies Workflow

## Overview

Run Charlie's explicit end-to-end delivery workflow with rigor proportional to
scope and risk. Feature Track changes an established product. Project Track
takes a greenfield product or MVP through discovery and vertical milestones.

This skill is opt-in only. Use it only when the user explicitly invokes
`$charlies-workflow`.

## Operating Contract

- Keep discovery, spec, plan, implementation, verification, documentation,
  review, and publication as distinct phases.
- Read only the current action before running it. Do not preload every action
  or helper skill.
- A later phase may start only after the current action's Exit Test passes.
- Interactive approval is the default. An explicit `auto`, `autonomous`, or
  `no questions` request selects autonomous approval without removing any spec,
  plan, TDD, verification, documentation, or review gate.
- All planning happens in the current conversation. Never move the workflow to
  a separate planning experience or treat planning as an implementation step.
- Use inline execution by default for tightly coupled work. Ask once about
  inline versus subagents only when either is genuinely viable and the user has
  not already chosen.
- Keep current-run workflow artifacts ignored and temporary. Preserve only
  source-final behavior and durable decisions in canonical documentation.
- Create a draft PR by default. Never merge, deploy, or perform another
  irreversible external action without explicit authorization.

## Precedence and Ownership

Apply rules in this order:

1. Explicit user requirements and repository safety instructions.
2. A project-specific child workflow such as `em-workflow`.
3. This workflow's phase, approval, artifact, and publication gates.
4. Selected helper skills within the phase they own.

Charlie owns sequencing and gates. `brainstorming` owns discovery technique,
`writing-plans` owns plan quality, TDD owns the RED/GREEN loop, UI skills own
design critique, `doc-it` owns documentation quality, and PR skills own PR text.
A helper may not change the selected track, skip a gate, commit temporary
artifacts, or broaden its phase.

`No blocking questions` is a discovery conclusion backed by repository facts
and explicit assumptions, never a shortcut around the discovery action.

## Action Router

Run every action in order. Before each action, read that file and only the
references it explicitly requires.

| # | Action | Outcome |
| --- | --- | --- |
| 1 | [Ground and Route](actions/01-ground-and-route.md) | Repo truth, track, tier, mode, skills, and run state |
| 2 | [Discover and Spec](actions/02-discover-and-spec.md) | Decision-complete intent and approved proportional spec |
| 3 | [Plan](actions/03-plan.md) | Separate implementation plan derived from the approved spec |
| 4 | [Implement](actions/04-implement.md) | Focused TDD implementation without requirement drift |
| 5 | [Verify and Document](actions/05-verify-and-document.md) | Final checks, browser evidence, durable docs, and artifact cleanup |
| 6 | [Review and Publish](actions/06-review-and-publish.md) | `ship` verdict on current HEAD, final report, and draft PR |

The normal state progression is:

```text
grounding -> discovery -> awaiting-spec-approval -> planning -> implementing
-> verifying -> documenting -> reviewing -> publishable -> published
```

On `iterate`, return to implementation, rerun only invalidated checks, and
review the new candidate HEAD. On a genuine human-only blocker, stop and report
the exact unmet condition.

## Track and Tier Routing

Choose track before tier:

| Track | Use when |
| --- | --- |
| Feature Track | Fixing, extending, or refactoring an existing product or repository |
| Project Track | Creating a separate greenfield product or MVP through an agreed completion state |

- Honor an explicit track.
- Default existing repositories to Feature Track and empty/starter products to
  Project Track. Ask when both remain plausible in interactive mode.
- For Project Track, read [project-track.md](references/project-track.md).
- A child workflow may restrict itself to Feature Track.

Then classify the current feature or Project Track milestone:

| Tier | Typical shape |
| --- | --- |
| Small | One clear low-risk surface with localized behavior |
| Medium | Several related files or states with moderate regression risk |
| Complex | Cross-package work, independent workstreams, or material security, permissions, payments, migration, infrastructure, or rollout risk |

Small work uses a concise in-conversation brief and plan. Medium and Complex
work use separate temporary spec and plan files. User instructions may demand
more rigor, but risk-sensitive work may not be downgraded merely to reduce
ceremony.

## Minimal Skill Routing

Load a helper only when the current action needs it:

- `brainstorming` / `superpowers:brainstorming`: non-trivial discovery and spec.
- `writing-plans` / `superpowers:writing-plans`: Medium and Complex plans.
- `test-driven-development` / `superpowers:test-driven-development`: behavior changes.
- `using-git-worktrees` / `superpowers:using-git-worktrees`: requested isolation,
  dirty checkouts, or PR-bound work.
- `emil-design-eng` and `ui-ux-pro-max`: meaningful UI and the required
  responsive quality gate.
- `hallmark`: only under [hallmark-routing.md](references/hallmark-routing.md).
- `playwright-interactive` or `playwright`: browser verification.
- `doc-it`: targeted durable documentation review.
- `pr-title-and-description`: PR publication.

Use `subagent-driven-development` only after the plan is ready and only for
genuinely independent tasks. A worker receives one bounded deliverable and may
not edit the spec, acceptance criteria, or plan.

## Temporary State and Artifacts

For Medium and Complex work, copy
`assets/run-state-template.json` into the current run directory, normally
`output/workflow/<run-id>/`. Verify that location is ignored before writing. If
the repository has no ignored workflow location, use an OS temporary directory
instead of changing `.gitignore` solely for workflow artifacts.

Update state only after the relevant Exit Test passes. The spec, plan, review
notes, and state are execution aids. Remove them before publication after the
decision-promotion gate. Never stage them, commit them, or retain them under
`docs/superpowers/` unless the user explicitly requests a canonical design
artifact and the documentation gate selects an appropriate permanent home.

## Hard Gates

Production edits are blocked until the selected track and tier are recorded,
discovery is complete, the proportional spec is approved or explicitly
not-required, and the separate plan is ready or explicitly not-required.

Publication is blocked until:

- TDD or a documented user-approved exception is recorded.
- Final verification applies to the current candidate HEAD.
- Meaningful UI passed functional browser QA and Verify Beyond the Obvious.
- Documentation has one final status: `changed`, `current`, `not-needed`, or
  `declined-with-gap`.
- Temporary artifacts are absent from the final diff and branch history.
- Consolidated review returned `ship` for the exact current `reviewed_head`.
- The worktree contains no unreviewed source changes.

Pending generic CI or external reviewers may be reported after one query unless
the user or a child workflow requires waiting for a terminal result.

## Common Failure Modes

| Failure | Correction |
| --- | --- |
| Counting questions instead of resolving decisions | Continue the discovery readiness loop until no build-changing item remains open |
| Treating `no questions` as permission to skip planning | Use autonomous approval while preserving every artifact and quality gate |
| Writing the plan before approval | Return to Discover and Spec; planning consumes an approved spec digest |
| Quietly changing requirements during implementation | Invalidate the spec approval, revise, and replan |
| Treating green tests as complete browser proof | Run functional QA and the separate responsive quality gate |
| Reviewing a stale diff | Review again and replace `reviewed_head` |
| Keeping workflow transcripts as permanent docs | Promote only durable source-final behavior or non-obvious decisions |
| Letting a child workflow duplicate Charlie | Keep the child as a narrow override layer |
