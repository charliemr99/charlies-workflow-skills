# Ground and Route

## Input

User request, repository context, and any existing run state.

## Output

Grounded track/tier/approval mode and verified discovery state.

## Process

1. Inspect repository instructions, Git status/base, affected flow, callers,
   tests and contracts. Reuse current evidence; expand reads to resolve unknowns.
   Preserve unrelated changes and isolate work when required. Use the worktree
   helper only if setup needs its technique; do not install dependencies blindly.
2. Select track and tier using the entrypoint. Risk overrides patch size.
   Honor existing approval mode and authorization. Choose inline execution by
   default; do not ask a routine mode question.
3. Ponytail routing is automatic: for material simplification signals or explicit
   use, read [ponytail-routing.md](../references/ponytail-routing.md); otherwise
   record `ponytail_routing: auto`, `ponytail_mode: off` and a short reason.
   Never auto-select `ultra`. Do not ask a separate Ponytail mode question.
4. Small Feature Track returns to the entrypoint's compact route. For Medium or
   Complex, copy the state template into the verified ignored canonical run
   directory, or OS temp when unavailable. Record routing and `phase: discovery`;
   verify the file exists and parses before action 02 or discovery questions.
   Source/configuration edit restrictions do not prohibit ignored workflow state.
5. Select helpers only for a concrete current need, resolving their location via
   [helper-loading.md](../references/helper-loading.md). Do not preload them.

## Exit Test

Track, tier, approval mode and isolation are grounded; no source edits occurred.
Medium/Complex state exists, parses and records discovery. Advance to action 02.
