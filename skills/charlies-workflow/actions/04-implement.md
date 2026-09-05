# Implement

## Input

Approved spec and ready plan with valid digest binding.

## Output

Completed scoped behavior and one current evidence ledger.

## Process

1. For each behavior change, witness a meaningful failing test for the expected
   reason before implementation. Implement the smallest complete behavior, run
   GREEN, then refactor without changing acceptance criteria. Load the TDD helper
   only when its technique is needed; RED/GREEN remains mandatory without it.
2. Pure content, formatting, or generated non-behavior changes use direct checks
   with TDD recorded as not applicable. A behavior-change TDD exception requires
   documented user approval. Do not delete unrelated/pre-existing code to satisfy
   a helper's restart instructions.
3. Stay within approved intent. Implementation details already covered by the
   spec do not restart discovery; material requirement changes do. Ponytail may
   simplify implementation, never remove approved behavior or proof.
4. Run focused checks as changes land; batch independent checks while preserving
   RED-before-implementation ordering. Run broader required coverage at the
   stable candidate, avoiding the same full suite at every task/phase.
5. Update the existing proof mapping with outcome, tested content/command and
   artifact path. Store full logs externally or ignored; report failure excerpts
   and counts. Update changed state fields, not full copies of spec/plan/logs.
6. If independent workers were authorized, give bounded paths/interfaces and
   acceptance IDs with relevant context. Workers may not edit approved spec,
   acceptance criteria, plan or shared run state. The parent integrates and checks.

## Exit Test

Planned behavior is complete without requirement drift; required RED/GREEN and
focused regressions are recorded. Advance to verifying.
