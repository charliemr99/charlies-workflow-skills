---
name: charlies-content-workflow
description: Use when the user explicitly invokes $charlies-content-workflow for an evidence-backed short-form content lifecycle; do not use for an ordinary caption rewrite, translation, or one-step media edit
---

# Charlie's Content Workflow

## Purpose

Run a thin content-production overlay on `charlies-workflow`. Produce honest,
evidence-backed short-form content without duplicating Charlie's generic
software-delivery lifecycle.

## Activation Boundary

This workflow is explicit-only. Use it only when the user invokes
`$charlies-content-workflow` or `/charlies-content-workflow`. A caption rewrite,
standalone translation, isolated clip trim, or other one-step media edit does
not implicitly activate the full lifecycle.

## Parent Handoff

Load `charlies-workflow` first and inherit the user's interactive or autonomous
mode. The parent owns generic discovery, approvals, risk routing, run state,
worktrees, TDD, verification, durable documentation, exact-HEAD review, and
draft PR delivery. This child owns the content brief, source and claim ledgers,
evidence decisions, editorial package, production guidance, audiovisual QA,
handoff, and publication authority boundary.

Store the content brief, source ledger, claim ledger, asset/readiness ledger,
shot matrix, and final QA evidence with the parent's ignored run artifacts.
Never copy the parent's action files or create a parallel generic lifecycle.

## Scope Routing

Select the smallest scope that satisfies the request:

1. Strategy and research only.
2. Evidence-backed pre-production package.
3. Full production and master delivery.
4. Refresh or re-version of an existing piece.

Record the chosen scope, expected deliverables, available material, missing
material, and explicit publication boundary before production. Benchmarks and
HyperFrames are optional routes, never mandatory for every request.

## Content Gates

### 1. Brief and Research Gate

Read [content-brief-and-research.md](references/content-brief-and-research.md).
Settle audience, platform, promise, CTA, language variants, assets, freshness,
and the dated source ledger before approving content intent.

### 2. Claim and Evidence Gate

Read [claims-and-evidence.md](references/claims-and-evidence.md). Classify every
claim, block unsafe wording, and choose the smallest honest evidence path.
Approve the claim ledger before the final script. Run a benchmark only when a
benchmark claim requires it.

### 3. Editorial and Production Gate

Read [production-and-hyperframes.md](references/production-and-hyperframes.md).
Build the exact shot matrix from approved claims, time English and Spanish
separately, and use natural recorded audio as the edit master clock. Route each
shot to real footage, attributable evidence, A-roll, VO, or optional graphics.

### 4. Final Master and Handoff Gate

Read [final-av-qa-and-handoff.md](references/final-av-qa-and-handoff.md). Treat
compiled masters, not previews, as proof. Reconcile every visible and spoken
claim, verify the encoded outputs, and prepare a language-specific handoff.

## Specialist Routing

Use research, watch, social-content, media, HyperFrames, caption, audio, and
browser tools only for the portion they own and only when available. Tool
absence does not authorize fabricated evidence. HyperFrames is appropriate for
deterministic evidence graphics; real footage or a static card may be smaller
and more honest.

## Authority Boundary

Preserve originals and private media. Do not publish, host, upload, share to
Notion, send messages, synthesize the creator's voice, or automate social
distribution without separate explicit authority. A completed local master or
draft PR is not publication approval.
