# Implement

## Input

- Approved spec or brief, including its fingerprint when file-backed.
- Ready implementation plan and exact repository commands.
- Protected worktree and initialized verification ledger.

## Output

- The planned behavior implemented through a witnessed TDD cycle.
- Focused tests passing without unapproved requirement drift.

## Process

1. Load `test-driven-development` /
   `superpowers:test-driven-development` for every behavior change.
2. Treat the approved spec, acceptance criteria, and plan as immutable inputs.
   If implementation evidence requires a material change, stop, invalidate
   approval, and return to Discover and Spec before replanning.
3. Work one bounded behavior at a time:
   - RED: add the smallest meaningful failing test and run it. Confirm it fails
     for the expected missing behavior, not for setup noise.
   - GREEN: implement the smallest complete behavior and rerun the focused
     test.
   - REFACTOR: improve structure only while all relevant focused tests remain
     green.
4. When Ponytail is active, apply it only after tracing callers and ownership
   boundaries. Prefer repository reuse, standard-library or native behavior,
   installed dependencies, and one shared root-cause fix. Deliver the smallest
   complete behavior that satisfies every approved acceptance criterion;
   never simplify away planned evidence or safety.
5. Use repository patterns and domain libraries. Keep edits within the planned
   ownership boundaries and avoid opportunistic refactors.
6. Run narrow static checks during the loop when they catch local mistakes
   cheaply. Save broad regression checks for the final candidate.
7. Update the verification ledger with command, outcome, affected behavior,
   and evidence. A source change invalidates prior evidence for impacted paths.
8. When subagents were selected, give each one a bounded deliverable. Workers
   may not edit the spec, acceptance criteria, implementation plan, or workflow
   state.

## Exit Test

- Every planned implementation task is complete.
- Each behavior change has credible RED and GREEN evidence or a documented,
  user-approved exception.
- Focused tests pass and no material requirement drift remains unresolved.
- The state advances to `verifying`.
