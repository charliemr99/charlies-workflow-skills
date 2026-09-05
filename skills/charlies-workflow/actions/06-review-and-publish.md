# Review and Publish

## Input

Source-final diff, approved acceptance IDs, proof ledger, documentation status,
and publication constraints.

## Output

Exact-HEAD review, draft PR or requested local delivery, and concise final report.

## Process

Use the gates in [documentation-and-artifacts.md](../references/documentation-and-artifacts.md);
reuse that reference if already loaded. Artifacts are retained through review
loops, publication and required child checkpoints.

### 1. Review Candidate

1. Complete durable decision promotion before freezing the candidate. Stage only
   intended source/canonical docs and verify artifact safety. Commit the candidate.
2. Review the exact HEAD against the spec, plan and existing ledger across
   `functional` (acceptance and failure/downstream proof), `code` (correctness,
   regression/security/contracts/conventions), and `relevancy` (scope, duplication,
   unnecessary abstraction and fit). Reference evidence; do not copy all artifacts
   into another review report. No unreviewed source changes may remain.
3. When Ponytail was active or material complexity signals arise, apply
   [ponytail-routing.md](../references/ponytail-routing.md) and `ponytail-review`
   to this candidate. Feed findings into relevancy; record
   `simplicity_review_status` as not-selected, lean, findings-addressed or unavailable.

### 2. Ship Verdict

4. Use the strictest verdict: `ship` only when all axes pass, otherwise `iterate`
   with concrete findings. On iterate, retain artifacts, fix findings, rerun
   invalidated checks and review the new HEAD. If review changes a durable
   decision, update its canonical documentation before the next candidate.
5. Record exact `reviewed_head` and actual `verification_head`, including any
   demonstrated unchanged-source relation. Never transfer ship across a new HEAD.

### 3. Identity and Publication

6. For a requested local-only delivery, skip GitHub steps. Otherwise determine the
   expected GitHub account from user instructions, repo instructions, then known
   authenticated access/provenance. Resolve genuine ambiguity with the user.
   Owner equality is not required for an organization-owned repository. Verify
   `gh api user --jq .login`; switch accounts only with user authorization.
7. Prepare accurate PR text, using `pr-title-and-description` if needed. Confirm
   HEAD equals `reviewed_head`, worktree/index have no unreviewed changes, and
   artifact safety still holds. Reuse unchanged history evidence; changed HEAD,
   base, artifact paths or staging require the relevant safety checks again.
   Open a draft PR by default. No merge or deployment without authorization.
8. Query generic CI/external review once; wait for terminal results only when
   required by user/child rules. Pending CI is not a passing result. Publication
   or required-check failures preserve resume state and are reported accurately.

### 4. Terminal Cleanup and Report

9. After successful requested delivery and required child checkpoints, apply the
   Post-ship Artifact Cleanup Gate. For explicit local-only delivery this follows
   final local review. Preserve evidence linked in the handoff outside disposable
   artifacts. Never clean resume state while delivery is blocked.
10. Report outcome, meaningful verification, final documentation status/links,
    final SHA/PR and any outstanding risks or checks. Omit irrelevant empty slots
    and routine gate narration. Local completion must not be called published.

## Exit Test

Ship covers exact final HEAD, requested delivery is evidenced, required child
checks are complete, and this run's disposable artifacts are cleaned. Otherwise
report the precise remaining condition and preserve state.
