# Compatibility and Evidence Boundaries

This package is Codex-first and portable by the Agent Skills format. The source
skills stay within the strict Agent Skills frontmatter schema; harness-specific
invocation extensions are added only to installed copies.

## Harness Matrix

| Harness | Project discovery root | User discovery root | Explicit invocation | Installer behavior |
|---|---|---|---|---|
| Codex | `.agents/skills` | `~/.agents/skills` | `$charlies-workflow` | Preserves strict source frontmatter and `agents/openai.yaml` policy |
| Claude Code | `.claude/skills` | `~/.claude/skills` | `/charlies-workflow` | Adds `disable-model-invocation: true` to explicit-only installed copies |
| Cursor | `.agents/skills` | `~/.agents/skills` | `/charlies-workflow` | Adds `disable-model-invocation: true` to explicit-only installed copies |

The installer does not mutate source skills. A custom `--target-dir` uses the
Codex adapter unless `--harness claude` or `--harness cursor` is supplied.
Legacy Codex locations remain available through an explicit custom target, but
the package defaults to the current shared `.agents/skills` root.

## Invocation Policy

`charlies-workflow` and standalone Hallmark are explicit-only. Codex policy is
declared in each skill's `agents/openai.yaml`. Claude Code and Cursor receive
their equivalent top-level extension only after copying. Routed helpers remain
available for the parent workflow to select without disabling model invocation.

## Evidence Status

Normal validation proves package structure, dependency closure, activation
policy, reversible installation, and the ordered request-to-draft-PR contract.
The canonical lifecycle fixture is synthetic and labels itself
`deterministic-contract-fixture`; it cannot claim a model, browser, GitHub, or
harness actually performed the work.

Real Codex and Claude Code lifecycle runs have been measured; Cursor remains
pending. On 2026-08-23, Codex CLI `0.149.0-alpha.4.1` and Claude Code `2.1.132`
both completed discovery, spec approval, a separate plan, TDD delivery,
three-viewport browser verification, cleanup, and real draft PR publication
against the same immutable fixture and hidden oracle. See
[cross-harness E2E validation](e2e-validation.md).

The optional smoke runner remains labeled `model-driven-smoke-evaluation`, and
neither it nor the full lifecycle runner is executed by normal validation.
Passing schema and deterministic checks therefore proves package coherence;
the dated E2E evidence remains a separate, refreshable compatibility claim.

## Hallmark Network and Third-Party Asset Boundary

The Hallmark network and third-party asset boundary is explicit:

Hallmark's local design rules work offline. URL study, web asset discovery,
external brand material, and examples linked to the pinned upstream repository
may require network access. Third-party assets remain subject to their source
licenses and usage terms; bundling Hallmark does not grant rights to fetch,
copy, or publish those assets.

Ponytail is an optional external plugin. Its absence cannot block Charlie's
core lifecycle, and its repo-wide audit mode is never selected implicitly.

## Validation Layers

Each source skill is checked by:

1. package relationship, resource, link, and activation validators
2. deterministic lifecycle mutation tests
3. the commit-pinned Codex `quick_validate.py`
4. `skills-ref==0.1.1` through `agentskills validate`

The final layer is the Agent Skills reference schema. Harness-only extensions
are intentionally excluded from source before that validation runs.
