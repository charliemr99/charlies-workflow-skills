# Ground and Route

## Input

- The user's request and any explicit execution or approval constraints.
- The repository root, repository instructions, and current Git state.
- Existing workflow state when resuming a run.

## Output

- Selected `Feature Track` or `Project Track`.
- Selected `Small`, `Medium`, or `Complex` tier.
- Approval mode: `interactive` by default or `autonomous` only when explicitly
  requested.
- Execution strategy, minimal skill set, affected surfaces, and initialized run
  state.

## Process

1. Read repository instructions, package scripts, architecture notes, and the
   exact product surface before proposing changes.
2. Check Git status and preserve unrelated work. Use an isolated worktree when
   requested, when the checkout is dirty, or when the work will become a PR.
3. Search for existing implementations, tests, contracts, and documentation
   that constrain the request.
4. Select the track before the tier. Existing products normally use Feature
   Track; separate greenfield products or MVPs use Project Track. A child
   workflow may restrict the choice.
5. Classify risk, not just diff size. Authentication, authorization, money,
   migration, infrastructure, security, destructive behavior, and broad
   compatibility normally force `Complex`.
6. Select only the skills needed for the current phase. Record why each was
   selected.
7. For Medium or Complex work, initialize a run directory from
   `../assets/run-state-template.json`. Confirm the path is ignored, or use an
   OS temporary directory. Never modify `.gitignore` solely for workflow state.
8. Treat `no questions`, `auto`, or `autonomous` as an approval-mode choice.
   It does not remove discovery, spec, plan, TDD, verification, documentation,
   or review requirements.

Do not edit production code during this action.

## Exit Test

- Track, tier, approval mode, execution strategy, and selected skills are
  recorded.
- Repository truth, affected surfaces, constraints, and material risks are
  known well enough to begin discovery.
- Unrelated work is protected and the run state has advanced to `discovery`.
- No production file has been changed.
