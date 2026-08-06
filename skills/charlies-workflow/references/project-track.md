# Project Track

Use this reference only when Charlie's Workflow selected Project Track for a
new product, greenfield application, or MVP. Project Track defines the program;
each implementation milestone uses the base Feature Track.

## Hard Gates

Follow this state sequence:

```text
Project discovery complete
-> Product Framing approved
-> MVP Contract approved
-> Architecture and Delivery Roadmap approved
-> canonical project baseline current
-> current milestone spec approved
-> current milestone implementation plan ready
-> milestone implementation and verification
-> next milestone or project release gate
```

Do not select a stack or create a delivery roadmap before Product Framing and
the MVP Contract are approved. Do not scaffold a repository, edit production
files, or provision infrastructure before the Architecture and Delivery
Roadmap is also approved.

## 1. Project Discovery

Inspect any starter repository, briefs, assets, adjacent systems, organization
standards, and existing deployment conventions before asking discoverable
questions. When no repository exists, ground in the supplied materials and
workspace without inventing organizational standards.

Ask questions one at a time and cover every category:

| Category | Decisions to resolve |
| --- | --- |
| Problem and audience | Primary user, job to be done, pain, value proposition |
| Success | MVP outcome, measurable metrics, validation method |
| Scope | Must-have capabilities, non-goals, deferred ideas |
| Journeys | Critical end-to-end paths, roles, permissions, error recovery |
| Product constraints | Timeline, budget, content, localization, accessibility |
| Data and integrations | Data ownership, external systems, import/export, retention |
| Risk | Authentication, privacy, security, compliance, abuse, destructive actions |
| Technology | Existing preferences, supported platforms, hosting, compatibility |
| Visual direction | Brand assets, references, desired character, responsive needs |
| Operations | Environments, observability, support, rollout, rollback, ownership |
| Completion state | `prototype`, `launch-ready`, or `deployed` |

Do not optimize for a minimum question count. Optimize for decision coverage.
An unknown may remain only when it is written as an assumption with its impact,
default choice, and user approval.

Default completion state is `launch-ready`: tested, documented, deployable, and
ready for release approval. `deployed` includes provisioning and live smoke
verification but requires explicit approval of the target account/environment,
cost, credentials path, and rollback boundary before external changes.

Use `brainstorming` / `superpowers:brainstorming` for project shaping. Present
two or three viable product/technical approaches with tradeoffs and a
recommendation before finalizing the contract.

## 2. Product Framing

Before locking the MVP Contract, state the product bet in one reviewable frame:

- The opportunity, primary audience, painful job, and promised value.
- Evidence already available versus assumptions still being made.
- The riskiest assumption and the smallest credible validation check.
- The behavior or signal expected after a user receives the value.
- Why this product boundary is preferable to the considered alternatives.

Obtain explicit approval of Product Framing in interactive mode. Autonomous
mode may record an auto-approved framing only when the user explicitly selected
that mode. Product Framing is not a marketing brief; it constrains what belongs
in the MVP and what should remain outside it.

### Decision Spike

Use an optional Decision Spike only when one bounded uncertainty blocks
feasibility, architecture, estimation, or a material risk decision. A spike:

- asks one precise question and defines time, scope, and mutation boundaries;
- names the evidence needed and objective exit criteria;
- avoids production implementation and unrelated exploration;
- concludes `resolved`, `inconclusive`, or `blocked`; and
- folds the result into Product Framing, the MVP Contract, or the roadmap.

An inconclusive spike does not silently become permission to implement. Resolve
the uncertainty, change scope, or obtain explicit acceptance of the residual
risk.

### Optional Hallmark Discovery

Apply `hallmark-routing.md`. In Project Track, `hallmark study` may extract
visual DNA from a user-approved reference during discovery, but Hallmark is
still unnecessary when the product does not meet the routing conditions.

## 3. MVP Contract

Create a product-level spec that locks:

- Problem, audience, value proposition, and success metrics.
- Completion state and launch boundary.
- Critical journeys and capability map.
- Explicit MVP scope and non-goals.
- Roles, permissions, data responsibilities, and important failure behavior.
- Product, visual, accessibility, security, compliance, and compatibility
  acceptance criteria.
- Unknowns that remain intentionally deferred and why they do not block.

Present it in reviewable sections, self-review it for ambiguity, contradictions,
placeholders, and oversized scope, then obtain explicit approval. Approval of a
general idea is not approval of the written MVP Contract.

Store the temporary working contract under the ignored
`output/workflow/<project-id>/` location required by the base skill. Present and
approve it in the current conversation before deriving any implementation
plan.

## 4. Architecture and Delivery Roadmap

After the MVP Contract is approved, define:

- System context, major boundaries, and ownership.
- Stack and dependency choices with important constraints.
- Domain/data model, interfaces, integrations, and data lifecycle.
- Authentication, authorization, privacy, security, and abuse controls.
- Environments, configuration, migrations, deployment, rollback, and recovery.
- Logging, monitoring, analytics, support, and operational ownership.
- A sequence of vertical milestones that each deliver demonstrable behavior.

Each milestone must be independently testable and reasonably reviewable in one
PR. Avoid horizontal plans such as "build the entire database, then the entire
API, then the entire UI" when a vertical user journey can prove the architecture
earlier.

For each milestone record goal, user-visible outcome, dependencies, non-goals,
acceptance criteria, test/browser scenarios, documentation impact, and release
relationship. Obtain explicit approval of the architecture and milestone
roadmap before scaffolding or implementation.

## 5. Canonical Project Baseline

After all three project approvals, promote only the durable shared context
needed across milestones:

- A concise product/MVP contract in the repository's canonical product
  documentation location.
- A concise system overview in the canonical architecture location.
- Focused ADRs only for non-obvious decisions with lasting consequences.
- A lightweight milestone/status view only while multi-PR coordination needs
  it.

Use existing repository conventions. When none exist, default to
`docs/product/mvp.md`, `docs/architecture/system-overview.md`, and
`docs/decisions/` for ADRs.

Canonical files describe current intent, contracts, and implementation state.
They exclude question transcripts, TDD logs, approval history, file-by-file
plans, and PR choreography. Temporary project specs and implementation plans
remain ignored and are cleaned through the base artifact lifecycle.

## 6. Milestone Loop

For each approved roadmap milestone:

1. Re-ground against the current repository and canonical project baseline.
2. Apply the Feature Track's Small/Medium/Complex tier to this milestone.
3. Brainstorm unresolved milestone decisions and write a proportional spec.
4. Obtain explicit approval of the milestone spec.
5. Use `writing-plans` / `superpowers:writing-plans` to create a separate
   implementation plan from that spec.
6. Do not request another plan approval unless the plan introduces a product,
   architecture, security, migration, cost, or rollout decision absent from the
   approved specs.
7. Implement with focused TDD, proportional integration/browser coverage,
   documentation, decision promotion, consolidated review, and a draft PR.
8. Update the canonical baseline only with source-final behavior and durable
   decisions.
9. Reassess downstream milestones when implementation evidence invalidates an
   approved assumption; obtain approval for material scope or architecture
   changes.

Do not generate detailed implementation plans for all milestones up front.
Write the next milestone plan against the repository state that will actually
implement it.

## 7. Project Release Gate

When all in-scope milestones are stable, verify the approved completion state:

- Critical user journeys and cross-milestone integration.
- Empty, loading, error, retry, offline/degraded, and recovery behavior.
- Authentication, permissions, privacy, security, and abuse boundaries.
- Small mobile, tablet, and desktop responsive quality where UI exists.
- Keyboard/focus, accessibility basics, motion/reduced motion, console/log
  health, and useful visual artifacts.
- Migrations, seed/bootstrap behavior, backups, rollback, and data recovery.
- Performance budgets or representative measurements appropriate to the MVP.
- Analytics, observability, alerting, support, and ownership agreed in the
  contract.
- Setup, environment, deployment, operations, troubleshooting, and known-gap
  documentation.

When Hallmark was approved, run `hallmark audit` as advisory visual input before
the final browser session. Never treat Hallmark's text/code audit as runtime,
responsive, accessibility, or interaction proof.

For `prototype`, report what is intentionally non-production. For
`launch-ready`, prove deployability and state the explicit release action still
pending. For `deployed`, verify the live target, deployment version, critical
smoke paths, monitoring state, and rollback readiness.

The final project report maps the MVP Contract acceptance criteria to evidence,
lists delivered PRs/releases and canonical documentation, and states known
gaps, deferred capabilities, operational status, and the exact completion
state achieved.
