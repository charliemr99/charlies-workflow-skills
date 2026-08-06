# Review and Publish

## Input

- Verified source-final diff, acceptance criteria, evidence ledger, and
  documentation status.
- GitHub repository identity, publication constraints, and PR conventions.

## Output

- Consolidated review verdict for the exact candidate HEAD.
- A draft PR by default and a structured final delivery report.

## Process

1. Freeze the review candidate in a commit. Before committing, stage only the
   intended paths and verify temporary workflow artifacts are absent.
2. Review the candidate across three axes:
   - `functional`: every acceptance criterion maps to credible current
     evidence, including downstream and failure behavior.
   - `code`: correctness, regression risk, contracts, error handling, security,
     tests, maintainability, and repository conventions.
   - `relevancy`: scope discipline, duplication, unnecessary abstraction,
     repository rules, and whether the delivered behavior solves the approved
     problem.
3. Assign the strictest consolidated verdict: `ship` only when every axis
   passes; otherwise `iterate` with concrete findings.
4. On `iterate`, return to implementation, fix the findings, commit the new
   candidate, rerun invalidated checks, and review the new HEAD. Never carry a
   verdict across a source change.
5. On `ship`, store the exact commit as `reviewed_head` and the evidence
   identity as `verification_head`.
6. Before publication, verify that current HEAD equals `reviewed_head`, the
   worktree is clean apart from ignored runtime artifacts, and there are no
   unreviewed source changes.
7. Confirm the active GitHub identity matches the repository owner. Switch only
   with user authorization, and confirm again after switching.
8. Use `pr-title-and-description` to prepare an accurate title and body. Open a
   draft PR by default; do not merge or deploy without explicit authorization.
9. Query generic CI and external review once after publication. Pending results
   may be reported unless the user or a child workflow defines a stricter wait
   contract.
10. Produce a concise but complete final report containing:
    - executive outcome and user-visible behavior;
    - files or major surfaces changed and important decisions;
    - tests run with exact outcomes;
    - browser scenarios, all three viewport results, and artifact links;
    - skipped checks and blockers with reasons;
    - documentation status plus links to canonical docs;
    - spec and plan lifecycle status, normally `temporary and removed`;
    - consolidated review verdict and exact `reviewed_head`;
    - draft PR link and current CI/external-review state.

## Exit Test

- Consolidated verdict is `ship` for the exact current HEAD.
- The publication check finds no unreviewed source changes.
- The draft PR exists, or a user opt-out or exact publication blocker is
  documented.
- The final report links available evidence and the state is `published`.
