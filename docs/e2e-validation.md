# Cross-Harness E2E Telemetry Report

This report records the first controlled Charlie's Workflow lifecycle run in
Codex and Claude Code. It combines native harness logs, Decant `0.4.0`, GitHub
delivery data, independent tests, and a hidden browser oracle. Raw transcripts,
Decant databases, screenshots, and private fixture paths remain local under the
ignored `output/` directory.

## Executive Summary

- Both harnesses passed discovery, spec approval, a separate implementation
  plan, TDD delivery, independent verification, three responsive browser sizes,
  cleanup, and exact-head draft PR publication against the same fixture.
- Codex used `gpt-5.6-terra` at `xhigh`. Claude Code used
  `claude-opus-4-7[1m]`; its native telemetry also recorded one negligible
  `claude-haiku-4-5-20251001` helper usage entry.
- Claude completed the four-turn session in 15m 05.5s versus Codex's 33m 43.5s,
  a 55.25% wall-time reduction. It made 101 tool calls versus 151 for Codex.
- Native logs show Codex produced 76,100 output tokens across all four turns.
  The earlier 54,412 figure was Decant's delivery-turn value, not the complete
  multi-turn total.
- Cost is not comparable across harnesses in this run. Claude Code reported
  $7.6397 natively. Decant estimated $8.5817 for Claude and $6.0014 for Codex,
  but the Codex estimate omits discovery, spec, and plan usage.
- Both implementations passed the same hidden behavior contract. Codex changed
  5 files (+332/-4); Claude changed 15 files (+692/-21). Claude was faster and
  used fewer calls, while Codex produced the smaller maintenance footprint.

## Controlled Contract

- Fixture baseline: immutable private tag `fixture-v2`.
- Track and tier: Feature Track, Medium, interactive approval.
- One persistent harness session with four user turns: discovery, proposed
  spec, explicit spec approval and plan, then autonomous delivery.
- Source edits forbidden until the plan checkpoint passed.
- Delivery required TDD and UI checks at `390x844`, `768x1024`, and
  `1440x900`.
- Independent proof reran unit tests, lint, build, and a hidden Playwright
  oracle after the harness finished.
- Publication proof verified draft state, base branch, and exact PR head.
- Neither evidence PR was merged or deployed.

## Models And Runtime

Measured on 2026-08-23:

| Measure | Codex | Claude Code |
| --- | ---: | ---: |
| Harness version | `0.149.0-alpha.4.1` | `2.1.132` |
| Primary model | `gpt-5.6-terra` | `claude-opus-4-7[1m]` |
| Reasoning setting | `xhigh` | Not exposed |
| Provider | OpenAI | Anthropic |
| Session wall time | 33m 43.5s | 15m 05.5s |
| Sum of turn durations | 33m 39.2s | 14m 57.3s |
| Inter-turn runner gap | 4.3s | 8.2s |
| Native API time | Not exposed | 14m 33.7s |
| Native model turns | Not exposed | 106 |
| Decant message records | 512 | 266 |
| Context window | 258,400 | 1,000,000 |
| Peak context | 206,082 (79.75%) | 155,168 (15.52%) |
| Compactions | 0 | 0 |
| Subagents | 0 | 0 |

Decant message records are parsed log events, not equivalent conversational
turns. They should not be used as a productivity score.

Claude's native model ledger reported:

| Model | Direct input | Cache read | Cache write | Output | Native cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7[1m]` | 126 | 9,012,420 | 251,335 | 62,459 | $7.6392 |
| `claude-haiku-4-5-20251001` | 425 | 0 | 0 | 17 | $0.0005 |

The Haiku row appeared only in discovery and is auxiliary telemetry. The
workflow's primary responses and implementation were attributed to Opus.

## Time By Gate

| Gate | Codex wall | Codex TTFT | Claude wall | Claude API | Claude model turns |
| --- | ---: | ---: | ---: | ---: | ---: |
| Discovery | 1m 53.1s | 6.9s | 1m 13.7s | 1m 14.3s | 22 |
| Spec | 2m 11.6s | 28.6s | 1m 26.9s | 1m 26.3s | 5 |
| Plan | 3m 27.6s | 5.3s | 2m 22.2s | 2m 21.5s | 8 |
| Delivery | 26m 06.9s | 9.4s | 9m 54.5s | 9m 31.6s | 71 |

Delivery dominated both runs: 77.44% of Codex wall time and 65.66% of Claude
wall time. Claude's discovery API duration is 0.6s longer than its reported
wall duration; that is a native CLI accounting inconsistency, not corrected by
this report.

## Native Token Accounting

### Codex

Codex reports processed input and cached input together for each resumed CLI
turn. Reasoning output is a subset of output and must not be added again.

| Gate | Processed input | Cached input | Uncached input | Output | Reasoning output |
| --- | ---: | ---: | ---: | ---: | ---: |
| Discovery | 421,726 | 380,928 | 40,798 | 4,768 | 2,675 |
| Spec | 190,510 | 178,176 | 12,334 | 6,720 | 4,124 |
| Plan | 522,369 | 503,552 | 18,817 | 10,200 | 4,375 |
| Delivery | 18,760,681 | 18,540,672 | 220,009 | 54,412 | 24,656 |
| **Total** | **19,895,286** | **19,603,328** | **291,958** | **76,100** | **35,830** |

Cached input represented 98.53% of Codex's processed input. The large processed
total is repeated model context across calls, not 19.9 million unique prompt
tokens.

### Claude Code

Claude separates direct input, cache creation, and cache reads. The table below
covers the primary Opus usage returned by the four result records.

| Gate | Direct input | Cache read | Cache write | Output | Native cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Discovery | 22 | 565,738 | 39,731 | 4,918 | $0.6548 |
| Spec | 10 | 272,404 | 42,953 | 5,795 | $0.5496 |
| Plan | 13 | 563,738 | 12,558 | 10,319 | $0.6184 |
| Delivery | 81 | 7,610,540 | 156,093 | 41,427 | $5.8169 |
| **Total** | **126** | **9,012,420** | **251,335** | **62,459** | **$7.6397** |

Cache reads represented 97.29% of Claude's direct-plus-cache input accounting.
Claude produced 17.93% fewer primary-model output tokens than Codex across the
complete lifecycle.

## Tool Activity

| Gate | Codex calls | Claude calls |
| --- | ---: | ---: |
| Discovery | 11 | 20 |
| Spec | 3 | 4 |
| Plan | 8 | 7 |
| Delivery | 129 | 70 |
| **Total** | **151** | **101** |

Delivery accounted for 85.43% of Codex calls and 69.31% of Claude calls.

Codex exposes a unified `exec` tool to Decant. Native log inspection recovers
the nested operations:

| Codex nested operation | Calls |
| --- | ---: |
| `exec_command` | 111 |
| `apply_patch` | 32 |
| `view_image` | 4 |
| `write_stdin` | 4 |

Claude exposes its tools directly:

| Claude tool | Calls | Decant p50 | Decant p95 |
| --- | ---: | ---: | ---: |
| `Bash` | 36 | 165ms | 2,529ms |
| `Read` | 26 | 5ms | 10ms |
| `Write` | 18 | 5ms | 15ms |
| `Edit` | 13 | 5ms | 8ms |
| `TodoWrite` | 6 | 3ms | 3ms |
| `Skill` | 1 | 15ms | 15ms |
| `ToolSearch` | 1 | 2ms | 2ms |

Decant reported zero tool errors and zero MCP calls for both sessions. Browser
work executed through shell/native tools and the independent oracle, so zero MCP
calls does not mean browser validation was absent.

## Decant Economics

These values are Decant attributions, not native billing totals.

| Bucket | Codex generation | Codex cost/share | Claude generation | Claude cost/share |
| --- | ---: | ---: | ---: | ---: |
| Context | 28,048 | $5.1128 / 85.2% | 2,820 | $4.7136 / 54.9% |
| Planning | 24,656 | $0.8310 / 13.8% | 15,575 | $0.9517 / 11.1% |
| Code | 0 | $0.0000 / 0.0% | 16,365 | $1.2391 / 14.4% |
| Communicating | 1,708 | $0.0576 / 1.0% | 27,699 | $1.6773 / 19.5% |
| **Estimated total** | **54,412** | **$6.0014** | **62,459** | **$8.5817** |

Decant assigned the entire Codex run to orientation and zero tokens to
implementation, despite a 26-minute delivery turn and a published product diff.
Its Codex phase split is therefore unusable for this session. Claude received a
more plausible orientation/implementation split, but attribution remains an
estimate.

Decant attributed 33m 31.8s active and 10.0s waiting for Codex. For Claude it
attributed 15m 28.0s active and 8.3s waiting, which exceeds the 15m 05.5s wall
time. Bucket activity can overlap and must not be presented as literal elapsed
time.

## Cost Reconciliation

- Codex's native subscription run did not expose a monetary cost.
- Decant's Codex row contains only delivery-turn token totals: 220,009 uncached
  input, 54,412 output, and 24,656 reasoning output.
- Against the native four-turn totals, Decant undercounted Codex uncached input
  by 24.64% and output by 28.50%. Its $6.0014 is a partial estimate.
- Claude Code reported $7.6397 natively. Decant estimated $8.5817, 12.33% above
  the native amount.
- Therefore this run supports no valid statement that one harness was cheaper
  than the other.

## File And Delivery Footprint

| Measure | Codex | Claude Code |
| --- | ---: | ---: |
| Product files changed | 5 | 15 |
| Additions | 332 | 692 |
| Deletions | 4 | 21 |
| Commits | 2 | 1 |
| Independent unit tests | 2 passed | 24 passed |
| Harness-authored Playwright tests | 8 passed | 13 passed |
| Hidden oracle viewports | 3 passed | 3 passed |
| Draft PR exact-head check | PASS | PASS |

Decant emitted zero Codex file rows because Codex's unified `exec`
representation hides nested file operations from Decant. It emitted 40 Claude
path rows (26 reads, 13 edits, and 18 writes). This difference reflects adapter
visibility, not proof that Codex did no file work.

Claude introduced pure filter and URL-state modules plus broader test files.
Codex kept the implementation concentrated in the existing app and one browser
test file. Both passed the same hidden oracle, so the larger Claude diff is a
maintenance tradeoff rather than an automatic quality win.

## Quality Outcomes

| Check | Codex | Claude Code |
| --- | ---: | ---: |
| Discovery gate | PASS | PASS |
| Spec approval gate | PASS | PASS |
| Separate plan gate | PASS | PASS |
| Delivery gate | PASS | PASS |
| Independent unit/lint/build | PASS | PASS |
| Hidden browser oracle | PASS | PASS |
| 390x844 | PASS | PASS |
| 768x1024 | PASS | PASS |
| 1440x900 | PASS | PASS |
| Temporary artifact cleanup | PASS after evaluator correction | PASS |
| Draft-only, no merge/deploy | PASS | PASS |

The original Codex report was marked failed because the evaluator treated empty
ignored `output/workflow/` parent directories as retained artifacts. The
corrected rule checks only files and symlinks; the retained worktree recheck
returned `temporary_artifacts=false`. No product, test, browser, or publication
gate had failed.

## Data Quality And Limits

1. Native harness telemetry is authoritative for model, per-turn time, token
   categories, and native cost when available.
2. Decant is useful here for tool latency, file hotspots where the adapter
   exposes them, context peaks, and a second analytical view.
3. Decant ingested Claude with zero issues. Codex had one informational
   `unknown_record_type` issue and no failed records.
4. Codex emitted nonfatal CLI diagnostics about an experimental feature and a
   shortened skill-description budget. They were surfaced as error-shaped
   items but did not correspond to failed tool calls.
5. Token schemas differ materially. Codex processed input includes cached
   context; Claude splits direct input, cache writes, and cache reads. Do not
   compare only the `input_tokens` column.
6. Cost estimates are not subscription charges. The Codex estimate is partial,
   and Claude's Decant estimate differs from its native amount.
7. This is one controlled feature and one run per harness. It measures this
   lifecycle, model configuration, fixture, and date; it is not a general model
   ranking.
8. Cursor lifecycle validation remains pending.

## Runner Improvements From This Audit

The evaluator now records and reports:

- native model, harness version, reasoning setting, wall time, and context peak
- every resumed Codex turn instead of only Decant's last-turn token view
- Claude direct input, cache creation, cache reads, per-model usage, API time,
  model turns, and native cost
- per-gate token, time, tool-call, and cost data
- nested Codex operations and direct Claude tool types
- Decant model stats, bucket economics, phase attribution, file activity, tool
  latency, MCP calls, and ingest issues
- independent verification and browser-oracle durations for future runs
- product diff size and explicit native-versus-Decant discrepancy warnings

Future comparisons should warn when Decant differs from native output or direct
input totals, and should refuse cost rankings when either side lacks complete
native or estimator coverage.

## Local Evidence

The canonical ignored evidence directories are:

- `output/e2e/20260823T010410Z-codex`
- `output/e2e/20260823T020005Z-claude`

Each contains `report.md`, `report.json`, four turn transcripts, independent
verification logs, three browser screenshots, Decant exports, and the isolated
Decant database. These files intentionally remain untracked.
