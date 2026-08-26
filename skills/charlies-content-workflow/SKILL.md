---
name: charlies-content-workflow
description: Use when the user explicitly invokes $charlies-content-workflow for an evidence-backed short-form content lifecycle; do not use for an ordinary caption rewrite, translation, or one-step media edit
---

# Charlie's Content Workflow

## Purpose

Run a content-production overlay on `charlies-workflow`. The parent owns the
generic delivery lifecycle, approvals, run state, worktrees, tests,
verification, documentation, review, and draft PR. This child owns only the
content brief, evidence, production decisions, audiovisual proof, and
publication boundary.

This skill is explicit-only. Use it only when the user invokes
`$charlies-content-workflow` or `/charlies-content-workflow`.

## Scope

Select the smallest scope that satisfies the request:

1. Strategy and research only.
2. Evidence-backed pre-production package.
3. Full production and master delivery.
4. Refresh or re-version of an existing piece.

Load `charlies-workflow`, preserve its interactive or autonomous mode, and map
the selected content scope onto its phases. Do not copy or replace the parent's
generic lifecycle.

## References

- Read [content-brief-and-research.md](references/content-brief-and-research.md)
  while grounding the content request and researching sources.
- Read [claims-and-evidence.md](references/claims-and-evidence.md) before
  approving factual claims, demonstrations, or optional benchmarks.
- Read [production-and-hyperframes.md](references/production-and-hyperframes.md)
  when scripting, recording, capturing, editing, captioning, or creating
  optional HyperFrames graphics.
- Read [final-av-qa-and-handoff.md](references/final-av-qa-and-handoff.md) when
  verifying compiled masters and preparing the handoff.

Benchmarks and HyperFrames are optional routes, not default requirements.
Publishing, hosting, uploads, messages, and external sharing require separate
explicit authority.
