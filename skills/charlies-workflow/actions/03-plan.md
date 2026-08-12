# Plan

## Input

- The approved spec or Small-work brief.
- Its approval status and `spec_sha256` when file-backed.
- Current repository paths, commands, conventions, and risk tier.

## Output

- A separate, executable implementation plan derived from the approved spec.
- A recorded `plan_source_spec_sha256` for every file-backed plan.
- Traceability from each acceptance criterion to implementation work and
  verification evidence.

## Process

All planning happens in the current conversation. Planning is its own phase;
it does not happen implicitly while implementation begins.

1. Verify that the spec is still approved and its current digest equals
   `spec_sha256`.
2. For Small work, write a concise actionable plan in chat. It must still name
   exact surfaces, RED/GREEN tests, verification, and completion evidence.
3. For Medium and Complex work, load `writing-plans` /
   `superpowers:writing-plans` and create a separate temporary plan in the
   ignored run directory. Present the plan in the current conversation; the
   file is a working artifact, not a separate planning channel.
4. Project architecture onto exact files and ownership boundaries. Each task
   must state its purpose, expected behavior, implementation steps, focused
   test command, and completion signal.
5. When Ponytail is active, include a concise `simplicity proof` for tasks that
   may add dependencies, abstractions, or ownership surfaces: repository reuse
   searched, first viable Ponytail rung, and why lower-ownership options are
   insufficient. Skip this note when no real design choice exists.
6. Map every acceptance criterion to at least one task and one proof point.
7. Plan TDD explicitly: the failing assertion and reason for RED, the smallest
   GREEN implementation, and any justified REFACTOR step.
8. Plan unit and integration cases, edge/error behavior, browser scenarios,
   downstream impact, and final regression commands before implementation.
9. For meaningful UI, include the functional browser scenario matrix and the
   separate three-viewport quality review with named screenshots or artifacts.
10. Include documentation impact, rollout/rollback work, and temporary-artifact
   cleanup.
11. Reject placeholders and vague tasks such as "add tests" or "verify UI".
12. If the plan introduces a product, architecture, security, migration, cost,
    or rollout decision absent from the approved spec, return to discovery,
    revise the spec, obtain approval again, and regenerate the plan.

All production edits remain blocked until this action passes its Exit Test.

## Exit Test

- Plan status is `ready`, and a file-backed plan records the approved spec
  digest from which it was derived as `plan_source_spec_sha256`.
- Every acceptance criterion, risk, test case, browser scenario, artifact, and
  documentation obligation has an executable home in the plan.
- No new material decision bypassed spec approval.
- The state advances to `implementing`; production edits may now begin.
