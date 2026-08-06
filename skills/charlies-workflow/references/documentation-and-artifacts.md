# Documentation and Artifacts

Read this reference during Verify and Document, then reuse the review and
cleanup gates during Review and Publish.

## Contents

- Durable Documentation Gate
- Decision Promotion Gate
- Pre-review Artifact Safety Gate
- Post-ship Artifact Cleanup Gate
- Final Documentation Slot

## Durable Documentation Gate

Use final source, tests, and verified runtime behavior as evidence. The working
spec and implementation plan are not documentation sources of truth.

1. Inspect affected canonical documentation, including root Markdown symlinks,
   README/contributor/operator guides, the relevant `docs/` domain, and local
   documentation checks.
2. Add a compact documentation delta to the verification ledger:

   | Surface | Final evidence | Canonical target | Action | Verification |
   | --- | --- | --- | --- | --- |
   | Behavior/API/config/operations | file, test, or runtime | existing path or missing | update/create/current/not-needed | check or rationale |

3. Apply proportional rigor:
   - Small: use targeted `doc-it` when a durable surface changed; otherwise
     record `not-needed` with a concrete reason.
   - Medium: use targeted `doc-it` to audit affected canonical docs even when
     the result is `current`.
   - Complex: use targeted `doc-it` and cover applicable behavior, contracts,
     configuration, rollout, rollback, support, and troubleshooting. Record an
     explicit user decline as a gap.
4. Prefer the smallest canonical edit. Update an existing section first, add a
   section for the same audience and lifecycle, and create a page only when no
   canonical home exists or ownership is distinct.
5. Document only source-backed behavior, fields, commands, environment keys,
   states, errors, and examples. Flag unknowns instead of inventing them.
6. Run repository documentation checks when available. Otherwise verify links,
   paths, commands, identifiers, and examples manually against final source.

The ledger must end with exactly one status: `changed`, `current`,
`not-needed`, or `declined-with-gap`. Missing status, stale references, failed
checks, or a gap that affects setup, use, support, rollout, or recovery blocks
publication unless the user explicitly accepts it.

Permanent docs describe source-final purpose, behavior, contracts,
configuration, operations, troubleshooting, limitations, and verification.
Exclude approval history, task lists, TDD transcripts, commit choreography,
skill narration, and PR or automated-review instructions.

## Decision Promotion Gate

Run this only after consolidated review first returns `ship` for the exact
candidate HEAD. Keep the temporary spec, plan, state, review notes, and evidence
available while making this decision.

1. Never promote the implementation plan or its checklist.
2. Inspect the temporary spec for rationale that would be difficult to recover
   from final source, tests, and canonical docs.
3. Promote only enduring context: a non-obvious architecture tradeoff, rejected
   alternative with lasting consequences, cross-system contract, security or
   compliance rationale, migration/rollback constraint, or active multi-PR
   dependency.
4. When no promotion is warranted, record `Decision promotion: none` with a
   concrete reason.
5. When promotion is warranted, extract only the decision into the existing
   ADR, architecture, product, or design location that owns it. Do not copy or
   rename the spec wholesale.
6. A promoted decision is concise and source-final: status, implementation
   state, date, context, decision, material alternatives/tradeoffs,
   consequences, and links to canonical behavior or operations docs.
7. Keep a fuller design document only when the user/repository requires it,
   audit traceability requires it, or active multi-PR delivery still depends on
   it. Use a canonical non-workflow path.
8. If promotion changes tracked canonical documentation, commit that change,
   invalidate the prior `ship` verdict and affected evidence, and review the new
   HEAD while temporary artifacts remain available. Cleanup may start only when
   `ship` covers the final HEAD and promotion causes no further tracked change.

## Pre-review Artifact Safety Gate

Retain this run's plan, spec, run state, review notes, and necessary evidence
through consolidated review and every `iterate` loop. Keep them in the verified
ignored run directory or outside the repository. Never stage, force-add,
commit, or push them.

The final diff may not add, modify, rename, or copy files under
`docs/superpowers/plans/` or `docs/superpowers/specs/`. Deletions are allowed
only for an explicitly scoped cleanup. Restore a pre-existing artifact to its
base version; remove artifacts introduced by this run.

Before freezing each review candidate, set the intended PR base and known run
directory. Any tracked/history output or a failed ignore check blocks review:

```sh
BASE_REF=origin/main # replace when the intended PR base differs
RUN_DIR=output/workflow/<run-id> # replace with the actual ignored run directory
git log --format= --name-only --diff-filter=AMCR "$BASE_REF"..HEAD -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR "$BASE_REF"...HEAD -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR --cached -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git ls-files --others --exclude-standard -- \
  docs/superpowers/plans docs/superpowers/specs
git ls-files -- output/workflow
git check-ignore -q "$RUN_DIR" # only when RUN_DIR is inside the repository
```

Ignored temporary files are expected at this stage and are not a dirty source
tree. For an OS temporary directory, instead verify its resolved path is outside
the repository root. Inspect full `git status --short` separately so unrelated
or unintended changes still block the candidate commit.

## Post-ship Artifact Cleanup Gate

Run this only after `ship` covers the exact final HEAD and Decision Promotion is
final. First capture the final state fields needed in the delivery report. Then
delete this run's plan, working spec, run state, disposable evidence, and review
notes. Do not delete unrelated historical artifacts during an ordinary run.

Repeat the history, final-diff, staged, unstaged, untracked, and forced-tracked
checks from the pre-review gate. Also verify the known run directory is gone.
Any output blocks publication:

```sh
test ! -e "$RUN_DIR"
git log --format= --name-only --diff-filter=AMCR "$BASE_REF"..HEAD -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR "$BASE_REF"...HEAD -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR --cached -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git diff --name-only --diff-filter=AMCR -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git ls-files --others --exclude-standard -- \
  docs/superpowers/plans docs/superpowers/specs output/workflow
git ls-files -- output/workflow
```

Run this gate after cleanup, after staging, and immediately before push. Do not
use broad staging after it. A failed post-ship gate returns to cleanup; a source
change invalidates `reviewed_head` and returns to review.

## Final Documentation Slot

Every final report contains all six labels:

```text
Documentation
- Status: changed | current | not-needed | declined-with-gap
- Canonical files: <created, updated, or inspected paths>
- Decision promotion: none (<reason>) | <canonical path and promoted decision>
- Coverage: <durable behavior documented or reason no change was needed>
- Validation: <command or manual source evidence>
- Remaining gaps: none | <explicit gaps>
```

For `current` or `not-needed`, include inspected canonical paths and the
rationale. Never link a temporary spec or plan as delivery documentation.
