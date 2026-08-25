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
- Execution strategy, automatic Ponytail mode and reason, minimal skill set,
  affected surfaces, and initialized run state.
- For Medium and Complex work, a parseable
  `output/workflow/<run-id>/run-state.json` whose `phase` is `discovery`.

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
6. For coding work, evaluate the automatic simplicity routing in
   [`ponytail-routing.md`](../references/ponytail-routing.md). Keep
   `ponytail_routing` as `auto` unless the user explicitly selects or disables
   it. Record `ponytail_mode` and evidence-backed `ponytail_reason`; the maximum
   automatic intensity is `full`, and `ultra` always requires an explicit user
   request. Do not ask a separate Ponytail mode question. Use `unavailable`
   when relevant support cannot be loaded.
7. Select only the skills needed for the current phase. Record why each was
   selected. Load Ponytail only when the routing decision selects it and the
   helper is available, passing the exact selected intensity.
8. For Medium or Complex work, initialize
   `output/workflow/<run-id>/run-state.json` from
   `../assets/run-state-template.json`. Confirm the path is ignored, or use an
   OS temporary directory. Do not choose `.agents/`, `.claude/`, or another
   ignored folder when `output/workflow/` is available. Never modify
   `.gitignore` solely for workflow state. This ignored file is required
   workflow state, not production source or configuration. Set its grounded
   routing fields and `phase` to `discovery`, then parse or read it back.
9. Treat `no questions`, `auto`, or `autonomous` as an approval-mode choice.
   It does not remove discovery, spec, plan, TDD, verification, documentation,
   or review requirements.

Do not edit production code during this action.

## Exit Test

- Track, tier, approval mode, execution strategy, Ponytail routing decision,
  and selected skills are recorded.
- Repository truth, affected surfaces, constraints, and material risks are
  known well enough to begin discovery.
- Unrelated work is protected and the run state has advanced to `discovery`.
- For Medium and Complex work, the canonical `run-state.json` exists, parses,
  contains the selected routing values, and records `phase` as `discovery`.
- No production file has been changed.

Do not read `02-discover-and-spec.md` or ask discovery questions until every
Exit Test item above has observable evidence.
