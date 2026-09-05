# Verify and Document

## Input

Stable implementation, approved acceptance IDs, and accumulated proof.

## Output

Current verification and source-final documentation ready for review.

## Process

1. Run required repository checks and plausible regression coverage on the stable
   candidate. Record tested content/commit, relevant configuration/environment,
   command, result and artifact path in the existing ledger. Inspect failures.
2. Reuse proof only while its inputs remain unchanged. Source/config/environment
   changes invalidate affected proof; uncertain impact requires revalidation.
   A docs-only commit may reuse tests when tested source and relevant inputs are
   demonstrably identical. Preserve the original tested identity and record its
   relation to the candidate; never claim tests ran on a later HEAD.
3. For meaningful UI, use one browser session for functional QA and
   **Verify Beyond the Obvious**: keyboard/focus/accessibility, overflow/density,
   loading/empty/error states, themes and motion as relevant. Inspect small mobile
   (390x844), tablet (768x1024), and desktop (1440x900), capturing important states.
   One observation can support both gates; a screenshot alone does not prove
   behavior. Use browser helpers only when needed to operate the harness.
4. Choose `emil-design-eng` or `ui-ux-pro-max` only for a concrete unresolved
   design question or explicit requirement; neither full guide is a default load.
   Fix observed defects with regression proof, without unrelated redesign.
5. Read [documentation-and-artifacts.md](../references/documentation-and-artifacts.md).
   Complete the Durable Documentation Gate and Decision Promotion Gate before
   freezing the first review candidate so durable decisions share its review.
   Use `doc-it` only when the affected documentation needs its technique.
6. Retain ignored/external spec, plan, state and evidence through review,
   publication and required child checkpoints. Apply the Pre-review Artifact
   Safety Gate; temporary files must never enter commits/history.

## Exit Test

All acceptance IDs have current credible proof, required UI checks passed,
documentation has a final status, durable decisions are ready, and artifacts are
safe. Advance to reviewing; reuse this ledger instead of copying it.
