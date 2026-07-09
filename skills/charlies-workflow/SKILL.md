---
name: charlies-workflow
description: Use when the user explicitly invokes $charlies-workflow for a non-trivial feature, bug fix, refactor, UI change, or PR-ready implementation workflow
---

# Charlies Workflow

## Overview

Run Charlie's preferred feature workflow end to end: select relevant skills, understand the repo, plan with Superpowers, implement with TDD, verify thoroughly, document the change, and open a draft PR by default.

This skill is opt-in only. Use it when the user explicitly invokes `$charlies-workflow`; do not infer it from ordinary coding requests.

## Required Flow

### 1. Select Skills First

Before planning or editing, identify the skills that match the task and load them.

Always consider:
- `brainstorming` / `superpowers:brainstorming` for feature shaping, UI/product decisions, ambiguous requirements, or when the prompt is not decision-complete.
- `writing-plans` / `superpowers:writing-plans` for the implementation plan after the spec is approved.
- `test-driven-development` / `superpowers:test-driven-development` before writing production code.
- `using-git-worktrees` / `superpowers:using-git-worktrees` when the checkout is dirty, the work should be isolated, or the branch must be PR-ready.
- `executing-plans` / `superpowers:executing-plans` or `subagent-driven-development` / `superpowers:subagent-driven-development` when executing a written plan, depending on platform support and user authorization.
- `emil-design-eng` and `ui-ux-pro-max` for UI, UX, visual polish, frontend interaction, responsive behavior, animation, or design-system work.
- `doc-it` when docs need to be created or updated from code.
- `pr-title-and-description` before creating the PR.

If a relevant skill is unavailable, say so briefly and continue with the best local equivalent.

### 2. Ground in Repo Reality

Inspect before asking broad questions.

- Read repo instructions (`AGENTS.md`, `CLAUDE.md`, `README.md`, package manifests, test commands).
- Inspect the exact surfaces named by the user before adjacent files.
- Run `git status --short --branch`; protect unrelated edits.
- Search for existing patterns, tests, routes, schemas, and components before proposing new abstractions.

### 3. Brainstorm and Ask Questions

Do not jump from repo inspection straight into the implementation plan. First run an intent checkpoint and a real brainstorming pass.

After the first repo-context pass, summarize briefly:
- What the feature or fix appears to be.
- Which surfaces or subsystems look affected.
- What decisions are already locked by the prompt or repo.
- What assumptions would be risky to make.

For non-trivial work, ask at least one meaningful question round unless all of these are true:
- The user gave a specific target surface and desired behavior.
- Success criteria and non-goals are clear.
- Repo inspection found one obvious implementation path.
- No meaningful product, UX, data contract, permissions, rollout, testing, or PR-handling choice remains.

If no questions are needed, explicitly say `No blocking questions` and list the assumptions being locked before planning.

Question rules:
- Ask after inspecting discoverable repo facts, not before.
- Ask only questions that materially change scope, success criteria, UX, data contracts, rollout, testing, or PR handling.
- Prefer one question at a time for broad/creative work.
- For compact implementation tasks, ask a short batch of up to 5 high-impact questions.
- Prefer concrete options with a recommended default when possible.
- Cover success criteria, out-of-scope behavior, affected users/roles, edge cases, data/API contracts, UI states, browser-test expectations, rollout, and PR expectations when relevant.
- If a high-impact ambiguity remains, stop and wait for the answer before writing the implementation plan.
- If only non-blocking preferences remain, state the default assumption and continue.

For substantial feature shaping or UI/product work, use `brainstorming` / `superpowers:brainstorming` when available. If unavailable, perform the same behavior: explore context, ask questions, present 2-3 approaches with tradeoffs, recommend one, and get approval before writing the spec.

### 4. Write and Approve the Spec

Do not create the implementation plan until an approved spec exists.
The spec approval gate is required before implementation planning.

In normal execution mode:
- Write a Superpowers-style spec to `docs/superpowers/specs/YYYY-MM-DD-<feature>-design.md`.
- Include the relevant skills that shaped the spec and any design decisions taken from them.
- Include goal, success criteria, non-goals, users/roles, affected surfaces, data/API contracts, UI states, edge cases, failure modes, rollout notes, and verification expectations.
- Include a dedicated testing section with unit/integration scenarios and browser scenarios to cover.
- Self-review the spec for placeholders, contradictions, missing edge cases, and ambiguous requirements.
- Stop and ask the user to review/approve the spec before writing the implementation plan.

In Codex Plan Mode:
- Do not write files.
- Produce the spec as the approved chat plan first.
- Persist the spec file only after execution mode resumes.

### 5. Plan the Feature From the Approved Spec

Use `writing-plans` / `superpowers:writing-plans` only after the spec is approved.

The plan must lock:
- Goal, success criteria, and explicit non-goals.
- Chosen skills and why they apply.
- Files or subsystems to touch.
- Public interfaces, schemas, routes, commands, UI states, or data flow that will change.
- Unit/integration test cases, browser test scenarios, responsive UI/UX review viewports, screenshots/artifacts to capture, docs updates, and PR steps.
- Edge cases, failure modes, migrations, compatibility, and rollout constraints when relevant.

Browser testing must be planned before implementation, not decided only at the end. For user-facing UI, forms, auth, routing, async behavior, admin surfaces, responsive behavior, or visually risky changes, the plan must name the browser scenarios to test, the responsive UI/UX review viewports, and the screenshots/videos/logs to save.
Treat test scenario planning as part of the implementation plan, not as a final verification afterthought.

If the user asks for planning only, stop after the plan. If the user asks to implement end to end, continue after high-impact ambiguities are resolved.

### 6. Implement with TDD

Use `test-driven-development` / `superpowers:test-driven-development` for behavior changes.

- Write a failing test first, run it, and confirm the failure is for the expected reason.
- Implement the smallest production change that makes the test pass.
- Refactor only after green.
- Repeat for edge cases and regressions.
- If the repo has no realistic automated test seam, document why, add the closest practical regression coverage, and use manual verification as a supplement, not a replacement.

For UI work, apply `emil-design-eng` and `ui-ux-pro-max` during implementation, not only at review time.

### 7. Verify Beyond the Obvious

Run the planned narrow tests first, then broaden based on risk.

- Unit or integration tests for changed logic.
- Typecheck, lint, or build when the repo uses them and the touched area warrants it.
- Browser verification for the planned scenarios covering user-facing UI, routing, forms, auth flows, complex async behavior, or anything visually risky.
- Live or deployed checks only when the task is explicitly production/admin/deploy oriented or local verification cannot prove the contract.
- Save browser screenshots, videos, traces, or logs as artifacts/output files whenever browser testing runs.

When tests fail, fix valid failures in scope. Do not hide unrelated baseline failures; report them with evidence.

### 8. Responsive UI/UX Browser Review

For meaningful UI, UX, responsive, visual, animation, or interaction changes, run a separate browser review after functional verification.

Use `emil-design-eng` and `ui-ux-pro-max` for this review. Check at least three viewport sizes unless the surface cannot reasonably render at one of them:
- Small mobile, for example 375x667.
- Tablet, for example 768x1024.
- Desktop, for example 1440x900.

For each viewport:
- Exercise the main user path and at least one relevant edge, loading, empty, error, or overflow state when available.
- Check layout fit, information hierarchy, readable type, touch/click target size, spacing rhythm, focus states, disabled/loading states, contrast, and lack of horizontal scroll or content overlap.
- Check interaction polish using `emil-design-eng`: purposeful motion, responsive press feedback, no sluggish animation, no `transition: all`, correct transform origins for anchored UI, and reduced-motion behavior when motion is meaningful.
- Check UX quality using `ui-ux-pro-max`: accessibility basics, touch and interaction clarity, responsive layout, typography, color contrast, navigation/back behavior, and form feedback when relevant.
- Save a screenshot, video, trace, or log artifact for each viewport tested.

If this review is skipped, state why the change has no meaningful UI/UX surface or why the environment blocked browser review.

### 9. Document and Write the Final Report

Update project docs when behavior, setup, public APIs, admin workflows, commands, or operational procedures changed.

The final report must include:
- Executive summary of what changed and why.
- Files changed, grouped by behavior or subsystem.
- Important implementation decisions and alternatives considered.
- Tests run, including commands and results.
- Browser scenarios covered, with screenshots/videos/logs linked as artifacts/output files.
- Responsive UI/UX browser review results across at least three viewport sizes, with artifact links and any fixes made from that review.
- A browser artifact report with links to saved screenshots, videos, traces, or logs when browser testing ran.
- Skipped checks with reasons and any unrelated baseline failures.
- Spec and implementation-plan links.
- Docs updated or intentionally not needed.
- Draft PR URL and draft/merge status when GitHub work ran.

### 10. Create Draft PR by Default

After implementation, verification, and docs, prepare a draft PR unless the user explicitly opts out.

Before committing or pushing:
- Re-check `git status --short --branch`.
- Stage only intended paths with explicit `git add <path>...`.
- Use a conventional commit message.
- Generate PR title and body with `pr-title-and-description` from the diff vs base.

GitHub identity:
- Detect the intended account from repo instructions, user request, and local context.
- Always run `gh auth status` and `gh api user --jq .login` before PR creation.
- If a required account is clear and the active account differs, run `gh auth switch --hostname github.com --user <account>`, then rerun `gh api user --jq .login`.
- If the required account is unclear or unavailable, stop before push/PR and ask.

Create the PR as draft:

```bash
gh pr create --draft --base <base> --head <branch> --title "<title>" --body-file <body-file>
```

If the user explicitly asks to merge, squash merge, or address Gemini/GitHub comments, do that after the draft PR exists and after re-checking live PR state, checks, and review threads.

## Quality Gates

Do not call the workflow complete until:
- The selected skills were loaded or explicitly unavailable.
- The brainstorming/question checkpoint happened before the implementation plan.
- Any skipped-question decision included a `No blocking questions` rationale and explicit assumptions.
- The spec existed and was approved before the implementation plan.
- The implementation plan existed before production edits and was derived from the approved spec.
- New behavior has tests that failed before implementation, unless the user approved an exception.
- Unit/integration and browser scenarios were planned before implementation.
- Relevant automated and browser checks were run or explicitly reported as skipped.
- Meaningful UI/UX changes received a separate responsive browser review with `emil-design-eng` and `ui-ux-pro-max` across at least three viewport sizes.
- Browser artifacts were saved and linked when browser testing ran.
- Documentation/reporting is complete.
- Draft PR creation was attempted or intentionally skipped because the user opted out or GitHub identity/access was blocked.

## Common Failure Modes

| Failure | Required Correction |
| --- | --- |
| Starting code before repo inspection | Stop, inspect the real surface, then revise the plan. |
| Skipping questions because the task feels obvious | Run the intent checkpoint; ask high-impact questions or state `No blocking questions` with locked assumptions. |
| Writing an implementation plan before a spec | Stop, write/review the spec, get approval, then build the plan from it. |
| Planning tests only after implementation | Add unit/integration and browser scenarios to the implementation plan before coding. |
| Skipping TDD because the change is small | Write the narrow failing test or get explicit user approval for an exception. |
| Treating UI work as only CSS | Load UI skills and verify interaction, responsiveness, accessibility, and visual state. |
| Skipping responsive UI/UX review | Run the separate browser review with at least small mobile, tablet, and desktop viewport artifacts, or report why it is not applicable. |
| Final report only lists commands and PR | Include decisions, considered cases, browser artifacts, spec/plan links, skipped checks, and PR status. |
| Creating PR under the wrong account | Check `gh auth status` and `gh api user --jq .login`; switch and re-check before pushing. |
| Broad staging | Use explicit paths and re-check status before commit. |
| Reporting success with skipped checks hidden | Report skipped checks and why they were skipped. |
