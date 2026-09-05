# Documentation and Artifacts

Read during verification, then reuse for review and terminal cleanup.

## Durable Documentation Gate

Inspect the affected canonical README, guide, domain docs or root Markdown
symlink and applicable documentation checks. Use final source/tests/runtime as
truth, not the working spec. Keep one compact documentation entry in the existing
ledger: changed surface, evidence, canonical target, action and validation.

Update the smallest existing canonical section. Create a page only when there is
no appropriate home or distinct ownership requires one. Cover changed behavior,
contracts, configuration, operations, rollout/recovery and troubleshooting where
applicable. Use targeted `doc-it` only when that work needs its technique; tier
alone does not require it. Do not generate manuals or markers unrelated to scope.

Verify actual paths, identifiers, links, commands and examples; run required doc
checks. Final status is `changed`, `current`, `not-needed`, or `declined-with-gap`.
Missing/stale documentation or a gap affecting use, setup, support or recovery
blocks publication unless the user explicitly accepts it. Record remaining gaps
and approval; do not fill unknown behavior with invented documentation.

## Decision Promotion Gate

Run before freezing the first review candidate. Inspect the spec for enduring
rationale that cannot be recovered from source/tests/docs: material architecture
tradeoffs, rejected alternatives, cross-system contracts, security rationale,
migration/rollback constraints or active multi-PR dependencies.

Promote only such decisions to their canonical ADR/design/architecture home with
context, decision, consequences and source links. Never copy the working spec,
implementation plan, checklists or approval transcript. Keep a fuller design only
when requested, required for traceability or still needed for active delivery.
Otherwise record `Decision promotion: none` with its reason in the ledger.

Review may expose a new durable decision: update docs before the next candidate
and review the new HEAD. Promotion need not force a second review when it was
already included in the first candidate.

## Pre-review Artifact Safety Gate

Retain spec, plan, state, review notes and evidence in the verified ignored run
directory or outside the repo through review, publication and child checkpoints.
Never stage, force-add, commit or push them. Inspect full Git status for unrelated
changes; ignored run artifacts are not dirty source.

Before freezing a candidate, verify the intended PR base, actual run path and
artifact safety. Example checks, with actual paths substituted:

```sh
workflow_base=origin/main
workflow_run=output/workflow/<run-id>
git log --format= --name-only --diff-filter=AMCR "$workflow_base"..HEAD -- docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR "$workflow_base"...HEAD -- docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR --cached -- docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR -- docs/superpowers/plans docs/superpowers/specs output/workflow
git ls-files --others --exclude-standard -- docs/superpowers/plans docs/superpowers/specs
git ls-files -- output/workflow
git check-ignore -q "$workflow_run"
```

Any tracked/history output or failed ignore check blocks the candidate. Include
any additional actual artifact paths in those checks. For an external run path,
verify its resolved path is outside the repository instead of using check-ignore.
If no remote exists for authorized local delivery, use the verified starting
commit as the base. Do not invent a remote.

Final diffs may not add/modify/rename/copy workflow files under
`docs/superpowers/plans/` or `docs/superpowers/specs/`. Deletion is allowed only
for scoped cleanup. Preserve unrelated historical artifacts; do not rewrite
shared history to repair an accidental workflow commit without authority.

Bind this proof to candidate/base/paths. At publication, check current HEAD,
index and worktree and reuse history/diff proof if unchanged. Any relevant change
requires affected checks again. Do not broadly stage after checking.

## Post-ship Artifact Cleanup Gate

After ship covers final HEAD, requested publication/local delivery succeeds and
required child checkpoints complete, capture report values and clean only this
run's disposable spec/plan/state/logs/review notes. Preserve delivered evidence in
an ignored/external durable handoff location, with valid links, before cleaning.
If delivery is blocked, keep ignored resume state and explain the blocker.

Verify the disposable run directory is gone and HEAD/index/worktree still match
the reviewed candidate. Reuse unchanged safety proof; rerun affected checks if
cleanup changed tracked content, base or paths. A new HEAD always needs review.
Never delete unrelated historical artifacts or links promised in the handoff.

## Final Documentation Entry

Include status, relevant canonical links and coverage/validation in concise prose.
For current/not-needed, give the concrete rationale. Mention promoted decisions
and remaining gaps when present. Full evidence stays in its ledger/handoff;
never present a temporary spec or plan as permanent delivery documentation.
