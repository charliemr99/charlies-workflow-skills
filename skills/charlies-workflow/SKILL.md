---
name: charlies-workflow
description: Use when the user explicitly invokes $charlies-workflow for a greenfield project, MVP, feature, bug fix, refactor, UI change, or PR-ready implementation workflow
license: MIT
---

# Charlies Workflow

Deliver the requested outcome with rigor proportional to risk. This skill is
opt-in: use it only when explicitly invoked as `$charlies-workflow`.
Select the track, tier, context, helpers, and checks automatically; the user
never needs to request a Small or token-saving mode.

## Ownership and Approval

User requirements and repository safety instructions take precedence, followed
by a child workflow, Charlie's gates, and selected helpers. Charlie owns the
lifecycle; a helper supplies technique within its assigned phase.

Interactive spec approval is the default. Explicit `auto`, `autonomous`, or
`no questions` selects autonomous approval, preserving the quality gates.
Efficiency applies in either approval mode. Ask only for unresolved material
requirements or authority; reuse decisions and authorization already given.
`No blocking questions` must follow grounded discovery, not replace it.
Plan in the current conversation. Execute inline unless independent work and
existing authorization justify agents; do not ask a routine execution-mode question.

## Automatic Routing

Inspect repository instructions, Git state, affected code, callers, tests, and
contracts before choosing. Reuse known facts that are still current.

| Track | Use when |
| --- | --- |
| Feature Track | Changing an established repository/product |
| Project Track | Creating a greenfield product or MVP; read [project-track.md](references/project-track.md) |

Honor explicit track choices. Classify each feature or project milestone:

| Tier | Scope and risk |
| --- | --- |
| Small | One clear, localized, low-risk surface |
| Medium | Several related files or states with moderate regression risk |
| Complex | Cross-package work, independent workstreams, or material security, permissions, payments, migration, infrastructure, or rollout risk |

Risk overrides line count. Never downgrade to save tokens. Complex requires
complete risk coverage, not longer prose or loading every helper.

## Economy in Every Tier

- Search narrowly, read the affected flow and dependencies, and expand only to
  resolve a concrete unknown. Batch independent reads/checks within a phase.
- Keep each fact in one home: decisions and acceptance IDs in the spec; tasks
  and proof mapping in the plan; results in one evidence ledger; status and
  identity in run state. Reference these instead of copying between artifacts,
  chat, or reviewer prompts. Update changed fields, not the entire narrative.
- Plans specify interfaces, paths, meaningful failing assertions, commands, and
  completion criteria. Do not prewrite implementations or repeat the spec.
- Load a helper only for a concrete missing technique or an explicit mandate,
  not merely because of the phase/tier. Charlie's gate remains required without it.
- Keep full logs in ignored/external files. Return failures, counts, and evidence
  paths. Inspect every result; truncation or a skipped check is not success.
- Run required checks and plausible regression coverage. Repeat only when a
  source/configuration/environment change, failure, or unresolved risk invalidates
  evidence. Record the tested identity; never claim a test ran on a later HEAD.
- Keep updates about findings and decisions. Link artifacts instead of printing
  them. Final delivery includes relevant proof and limitations, without empty slots.
- Preserve the requested model and reasoning effort. Do not introduce arbitrary
  token budgets, stop unfinished work, or reduce acceptance criteria for savings.

## Small Route

For clearly Small Feature Track work, keep these outcomes distinct in concise
conversation entries; no spec/plan/state files or six-action tour is required.

1. **Brief:** outcome, scope, affected surface, acceptance and proof. Resolve
   material unknowns. A complete Small request with an explicit execution
   instruction supplies approval; otherwise obtain interactive approval or use
   existing autonomous approval. Do not silently invent a requirement.
2. **Plan:** a separate short sequence before production edits.
3. **Implement and verify:** witness meaningful RED/GREEN for behavior changes;
   directly validate non-behavior changes and record TDD as not applicable.
   Check affected docs. Meaningful UI still requires functional browser QA and
   Verify Beyond the Obvious at small mobile, tablet, and desktop sizes, using
   one browser session. Load action 05 if its detailed UI/doc gate is needed.
4. **Review and deliver:** assess functionality, code, and scope on the final
   diff, record documentation status and tested identity, and bind `ship` to the
   exact final HEAD. Use action 06 for PR publication or artifact handling.
   Respect publication opt-outs; otherwise create a draft PR.

Escalate to the full route immediately if grounding or implementation exposes
broader risk; earlier evidence may be reused if still applicable.

## Full Route: Medium, Complex, and Project Milestones

Read only the current action. Pass its Exit Test before advancing; do not
preload later actions or optional references.

| Action | Outcome |
| --- | --- |
| [01 Ground and Route](actions/01-ground-and-route.md) | Grounded routing and valid discovery state |
| [02 Discover and Spec](actions/02-discover-and-spec.md) | Decision-complete, approved spec |
| [03 Plan](actions/03-plan.md) | Separate implementation plan derived from approved spec |
| [04 Implement](actions/04-implement.md) | Focused TDD implementation |
| [05 Verify and Document](actions/05-verify-and-document.md) | Current proof and source-final durable docs |
| [06 Review and Publish](actions/06-review-and-publish.md) | Exact-HEAD review, draft PR, final report and cleanup |

For Medium/Complex, action 01 must copy `assets/run-state-template.json` into
`output/workflow/<run-id>/run-state.json` and verify parseable JSON with
`phase: discovery` before discovery questions or action 02. Verify the directory
is ignored first; use an OS temporary directory if it is not. Do not modify
`.gitignore` solely for this workflow or substitute another ignored repo folder
when the canonical location is available. Update state after each Exit Test.

Production edits require completed discovery, approved spec, and ready plan.
Bind Medium/Complex approval to `spec_sha256` and the plan to
`plan_source_spec_sha256`. Changed spec bytes invalidate the plan binding;
material requirement changes also invalidate approval and return to discovery.

## Conditional References and Helpers

Resolve a selected helper through [helper-loading.md](references/helper-loading.md).
Use `brainstorming`, `writing-plans`, TDD, worktrees, browser, design, `doc-it`,
or PR helpers only when their technique is needed. Gate obligations apply even
when no helper is loaded. For meaningful UI, choose `emil-design-eng` or
`ui-ux-pro-max` for the specific unresolved design question; do not load both by default.

Use [hallmark-routing.md](references/hallmark-routing.md) for a relevant brand,
redesign, or Hallmark request. Use [ponytail-routing.md](references/ponytail-routing.md)
when material simplification signals or explicit Ponytail instructions apply:
`ponytail` supplies implementation choices, `ponytail-review` feeds relevancy,
and `ponytail-audit` stays confined to an explicitly requested repo audit.
Never auto-select `ultra`. Otherwise record automatic routing as off with a reason.

## Delivery Invariants

Verification must cover the final candidate; documentation has one final status:
`changed`, `current`, `not-needed`, or `declined-with-gap`. Consolidated review
must return `ship` for the exact `reviewed_head`, with no unreviewed source changes.
On `iterate`, fix findings, rerun invalidated checks, and review the new HEAD.

Retain ignored/external spec, plan, state, and evidence through review loops,
publication, and required child checkpoints. They must stay unstaged and absent
from branch history. Promote durable decisions before freezing the review
candidate; clean disposable artifacts after terminal delivery. Use
[documentation-and-artifacts.md](references/documentation-and-artifacts.md).

Draft PR is the default; merge, deployment, and other irreversible actions
require explicit authorization. Query generic CI/review once unless user/child
rules require a terminal result. Report blockers precisely and preserve resume
state when delivery is blocked.
