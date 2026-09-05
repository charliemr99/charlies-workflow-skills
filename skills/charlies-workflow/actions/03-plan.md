# Plan

## Input

Approved spec and matching approval evidence/digest.

## Output

Separate executable plan bound to the approved spec.

## Process

1. Verify approved spec bytes still match `spec_sha256`. Create a separate plan
   file for Medium/Complex, recording `plan_source_spec_sha256`. Keep decisions
   and requirements in the spec; reference acceptance IDs from the plan.
2. For each bounded task, identify exact affected paths/interfaces, the acceptance
   criterion covered, meaningful RED assertion and expected failure, GREEN/check
   commands and completion evidence. Do not prewrite production code. Use
   `writing-plans` only when decomposition needs assistance.
3. Map every acceptance criterion to proof once. This mapping feeds one evidence
   ledger during execution; do not generate duplicate QA/review matrices.
   Meaningful UI needs a browser scenario for changed/failure behavior and
   small-mobile, tablet and desktop functional/visual proof. Include applicable
   security, migration, rollout and recovery checks for Complex work.
4. If Ponytail is selected, add a short simplicity proof for each material choice
   using its routing reference. Avoid ceremony for decisions already settled.
5. A new material requirement returns to discovery. Otherwise the approved spec
   authorizes its faithful plan; do not insert a second routine approval gate.
   Summarize sequence and unresolved constraints with a plan link.

## Exit Test

Every acceptance criterion has a task and credible proof; decisions are resolved,
plan status is ready and `plan_source_spec_sha256` matches approved spec bytes.
Until this Exit Test passes, production edits remain blocked. Advance to implementing.
