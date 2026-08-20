---
name: writing-plans
description: Use after an approved design to produce an executable, test-first implementation plan before touching code.
license: MIT
---

# Writing Implementation Plans

Turn an approved design into a decision-complete sequence of small, testable
deliverables. The plan is written for an engineer who understands software but
does not yet know this repository or feature.

## Parent Contract Integration

When selected by Charlie's Workflow, Charlie owns artifact location, approval
evidence, sequencing, execution strategy, final review, cleanup, and
publication. Apply this skill inside Charlie's Plan phase, follow Charlie's
artifact-retention policy, and return control to Charlie's Implement phase.
Do not choose a permanent path, request a second approval, or start code unless
the parent workflow explicitly requires it.

## Hard Gate

Planning begins only after the final design or proportional brief is approved.
Record the approved artifact path and digest in the plan. If the design changed
after approval, stop and return to discovery rather than silently planning a
different feature.

## Plan Process

1. **Read the approved artifact once.** Extract its acceptance criteria,
   constraints, non-goals, risks, rollout, and evidence requirements.
2. **Map repository surfaces.** Name every file to create, modify, test, or
   document and state its responsibility. Follow existing ownership boundaries.
3. **Define task interfaces.** State what each task consumes and produces,
   including exact symbols, schemas, routes, events, and state transitions.
4. **Right-size tasks.** Each task must deliver independently reviewable
   behavior with its own test cycle. Fold setup into the first task that uses it.
5. **Plan tests before implementation.** For every acceptance criterion, name
   the unit or integration test, the initial failing reason, the minimal change,
   and the passing command. Include negative, failure, permission, and boundary
   cases that can change the implementation.
6. **Plan browser evidence before implementation.** When a browser applies,
   define the starting state, actor, steps, assertions, data isolation, and
   screenshots, video, traces, or logs to retain. Meaningful UI work covers at
   least small mobile, tablet, and desktop viewports.
7. **Plan operational proof.** Include migrations, compatibility, observability,
   rollout, rollback, security, accessibility, and performance only where the
   approved design or repository risk requires them.
8. **Write exact steps.** Use executable commands, expected RED/GREEN outcomes,
   concrete file paths, and complete enough implementation guidance that no
   product decision is left to the implementer.
9. **Self-review against the design.** Map every acceptance criterion to at
   least one task and verification step. Remove gaps, contradictions, and
   accidental scope.
10. **Return to the parent.** Report the plan path, digest, source-design digest,
    task count, and unresolved execution risks. Do not begin implementation.

## Required Plan Header

Every plan starts with:

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]
**Architecture:** [Two or three concrete sentences]
**Tech Stack:** [Relevant tools only]
**Approved design:** [Path or conversation artifact]
**Approved design SHA-256:** [Exact digest]

## Global Constraints

- [Verbatim project-wide requirement]
```

## Required Task Shape

```markdown
### Task N: [Reviewable behavior]

**Files:**
- Create: `exact/path`
- Modify: `exact/path`
- Test: `exact/path`

**Interfaces:**
- Consumes: [Exact dependency]
- Produces: [Exact symbol or behavior]

- [ ] Write the failing test for [specific behavior].
- [ ] Run `[exact command]`; expect FAIL because [specific reason].
- [ ] Implement the smallest complete behavior in `[exact path]`.
- [ ] Run `[exact command]`; expect PASS.
- [ ] Run [targeted regression or browser scenario] and retain [artifact].
- [ ] Commit with `[exact message]` after the task review passes.
```

Use code snippets when an interface or algorithm would otherwise be ambiguous.
Do not paste speculative full implementations that the repository context may
invalidate.

## Test Matrix

The plan must make these relationships explicit:

| Requirement | Test level | Scenario | Expected result | Evidence |
|---|---|---|---|---|
| Acceptance criterion | Unit/integration/browser | Actor and steps | Observable assertion | Command or artifact |

If a level does not apply, record the concrete reason in the plan. Browser
testing is never deferred until the end as an unplanned judgment call.

## Plan Failures

Fix these before handoff:

- placeholders such as `TBD`, `TODO`, or "handle edge cases"
- an acceptance criterion without a named test
- commands without expected outcomes
- UI work without viewport and artifact coverage
- references to symbols, files, or dependencies no task creates
- a task that mixes unrelated deliverables
- a refactor with no demonstrated need in the approved design
- implementation or publication beginning inside the planning phase

## Execution Handoff

Return a compact handoff to the parent workflow:

```text
Plan ready: <path>
Plan SHA-256: <digest>
Source design SHA-256: <digest>
Tasks: <count>
Execution risks: <none or concrete list>
```

The parent decides whether work runs inline or through the bundled subagent
technique. In autonomous mode it continues without a routine execution-choice
question.
