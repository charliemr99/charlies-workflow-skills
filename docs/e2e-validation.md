# Cross-Harness E2E Validation

This document records the first controlled Charlie's Workflow lifecycle run in
Codex and Claude Code. Raw transcripts, Decant databases, screenshots, and
private fixture paths stay local under ignored `output/`.

## Contract

- Fixture baseline: immutable private tag `fixture-v2`.
- Track and tier: Feature Track, Medium, interactive approval.
- One persistent harness session with four user turns:
  discovery, proposed spec, explicit spec approval and plan, autonomous delivery.
- Source edits are forbidden until the plan checkpoint passes.
- Delivery must use TDD, verify `390x844`, `768x1024`, and `1440x900`, clean
  temporary workflow artifacts, and publish a draft PR without merge or deploy.
- Independent proof reruns unit tests, lint, build, and a hidden Playwright
  oracle. It also verifies draft state, base branch, and exact PR head.
- Decant `0.4.0` ingests the native harness session log after verification.

## Results

Measured on 2026-08-23:

| Measure | Codex | Claude Code |
|---|---:|---:|
| Harness version | `0.149.0-alpha.4.1` | `2.1.132` |
| Decant model label | `gpt-5.6-terra`, xhigh | `claude-opus-4-7` |
| Lifecycle gates | PASS | PASS |
| Independent unit/lint/build | PASS | PASS |
| Hidden browser oracle | PASS | PASS |
| Exact-head draft PR | PASS | PASS |
| Session wall time | 33m 43s | 15m 05s |
| Messages parsed | 512 | 266 |
| Output tokens parsed | 54,412 | 62,459 |
| Tool calls parsed | 151 | 101 |
| Decant estimated cost | $6.00 | $8.58 |
| Product diff | 5 files, +332/-4 | 15 files, +692/-21 |

The Codex run initially received a runner-only false failure because the
evaluator treated an empty `output/workflow/` directory as an artifact. All
lifecycle, publication, test, and browser gates had passed. The corrected rule
checks for files or symlinks, and the retained run recheck reports no temporary
artifacts.

## Findings

1. The spec approval and separate plan gates worked in both harnesses. Neither
   canonical run entered implementation before `plan-ready`.
2. Headless Claude `-p` did not reliably interpret a slash command as a loaded
   skill. The adapter now requires the native `Skill` tool explicitly.
3. Claude once loaded the skill but skipped run-state initialization. The
   workflow now makes `output/workflow/<run-id>/run-state.json` an observable
   Ground and Route exit condition before discovery.
4. Evaluators must compare semantics, not formatting accidents. Viewport checks
   now accept both `x` and the typographic multiplication sign, and cleanup
   ignores empty directory scaffolding.
5. Both implementations satisfied the same hidden behavior contract and looked
   sound at desktop and mobile sizes. Claude produced a more modular and broader
   test surface, but more than doubled the diff. That is a maintenance tradeoff,
   not an automatic quality win.

## Decant Limits

- Cost is Decant's estimate from model pricing, not a subscription charge.
- Token accounting differs by harness and cache representation; compare broad
  patterns, not billing totals.
- Decant tracked Claude file operations in detail. The Codex unified `exec`
  representation produced no file-operation rows and classified the whole run
  as orientation. File-level and phase-level comparisons are therefore not
  symmetric yet.
- E2E evidence is dated. Re-run it when harness versions, install adapters, or
  lifecycle gates change materially.

Cursor lifecycle validation remains pending.
