# Review and Publish

## Input

- Verified source-final diff, acceptance criteria, evidence ledger, and
  documentation status.
- GitHub repository identity, publication constraints, and PR conventions.

## Output

- Consolidated review verdict for the exact candidate HEAD.
- A draft PR by default and a structured final delivery report.

## Process

Read
[`documentation-and-artifacts.md`](../references/documentation-and-artifacts.md)
for the pre-review, decision-promotion, and post-ship cleanup contracts.

### 1. Review Candidate

1. Freeze the review candidate in a commit. Stage only intended source and
   canonical documentation paths. Apply the Pre-review Artifact Safety Gate:
   temporary workflow files remain available but must be ignored or outside the
   repository, unstaged, untracked by Git, and absent from the commit/history.
2. Review the candidate using the approved spec, implementation plan, run
   state, and evidence across three axes:
   - `functional`: every acceptance criterion maps to credible current
     evidence, including downstream and failure behavior.
   - `code`: correctness, regression risk, contracts, error handling, security,
     tests, maintainability, and repository conventions.
   - `relevancy`: scope discipline, duplication, unnecessary abstraction,
     repository rules, and whether the delivered behavior solves the approved
     problem.
3. Assign the strictest consolidated verdict: `ship` only when every axis
   passes; otherwise `iterate` with concrete findings.

### 2. Ship Verdict

4. On `iterate`, retain and update the temporary artifacts, return to
   implementation, fix the findings, commit the new candidate, rerun invalidated
   checks, and review the new HEAD. Never carry a verdict across a source change.
5. On `ship`, store the exact commit as `reviewed_head` and the evidence
   identity as `verification_head` in run state.

### 3. Decision Promotion

6. Only after `ship`, run the Decision Promotion Gate. If promotion changes
   tracked canonical documentation, commit it, invalidate `reviewed_head` and
   affected verification, and repeat review with the temporary artifacts still
   retained. Continue until `ship` applies to the source-final HEAD and decision
   promotion causes no further tracked change.

### 4. Artifact Cleanup

7. Capture the final state values needed by the delivery report, then delete
   this run's plan, working spec, run state, disposable evidence, and review
   notes. Run the Post-ship Artifact Cleanup Gate against the working tree,
   staged state, final diff, and branch history. Cleanup is blocked before
   `ship` and must not delete unrelated historical artifacts.
8. Verify current HEAD still equals `reviewed_head` and there are no unreviewed
   source changes.

### 5. GitHub Identity

9. Determine the expected GitHub account from, in order, an explicit user
   instruction, repository instructions, and authenticated access/provenance.
   Confirm with the user when those sources are ambiguous. Repository-owner
   equality is only a clue for personal repositories and is not required for an
   organization-owned repository. Verify `gh api user --jq .login` equals the
   expected account; switch only with user authorization and verify again.

### 6. Publish and Report

10. Use `pr-title-and-description` to prepare an accurate title and body. Open a
   draft PR by default; do not merge or deploy without explicit authorization.
11. Query generic CI and external review once after publication. Pending results
   may be reported unless the user or a child workflow defines a stricter wait
   contract.
12. Produce a concise but complete final report containing:
    - executive outcome and user-visible behavior;
    - files or major surfaces changed and important decisions;
    - tests run with exact outcomes;
    - browser scenarios, all three viewport results, and artifact links;
    - skipped checks and blockers with reasons;
    - documentation status plus links to canonical docs;
    - spec and plan lifecycle status, normally `retained through review, then
      removed after ship`;
    - consolidated review verdict and exact `reviewed_head`;
    - draft PR link and current CI/external-review state.

## Exit Test

- Consolidated verdict is `ship` for the exact current HEAD.
- Decision promotion is final, cleanup occurred after `ship`, and the
  publication check finds no temporary artifacts or unreviewed source changes.
- The draft PR exists, or a user opt-out or exact publication blocker is
  documented.
- The final report links available evidence and the state is `published`.
