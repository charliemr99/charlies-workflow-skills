---
name: brainstorming
description: Use during non-trivial discovery to resolve intent, constraints, approaches, and an approval-ready design before implementation planning.
license: MIT
---

# Brainstorming Ideas Into Designs

Turn an initial request into a decision-complete design through repository
grounding, focused questions, explicit tradeoffs, and user approval.

## Parent Contract Integration

When selected by Charlie's Workflow, Charlie owns artifact location, approval
evidence, sequencing, final review, cleanup, and publication. Apply this
skill's discovery and design technique inside Charlie's Discover and Spec
phase, use Charlie's proportional artifact rules, and return control to
Charlie's Plan phase. Do not commit a spec or choose a permanent path unless
the parent workflow or user explicitly requires it.

## Hard Gate

Do not implement, scaffold, or invoke an implementation skill until the design
or proportional brief has been presented and its parent approval gate passes.
The artifact scales with risk; the approval gate does not disappear.

## Process

1. **Ground in the repository.** Read the relevant product flow, nearby tests,
   conventions, documentation, and recent history before asking detailed
   questions.
2. **Build a decision ledger.** Cover outcome, actor, trigger, journey, visible
   behavior, scope, non-goals, state, interfaces, permissions, invariants,
   failures, edge cases, evidence, rollout, and rollback. Mark each item
   settled, open, or safely deferred.
3. **Ask only material questions.** Ask one coherent question at a time. Resolve
   the highest-impact unknown first and continue until no build-changing item
   remains open. Do not optimize for a question count.
4. **State assumptions.** `No blocking questions` is valid only when repository
   facts and explicit assumptions settle every material decision.
5. **Explore approaches.** When product shape or architecture has a meaningful
   choice, present two or three viable approaches with concrete tradeoffs and
   recommend one. Remove unnecessary scope from every option.
6. **Present the design.** Scale sections to their complexity. Cover ownership,
   components, data/control flow, error behavior, tests, browser evidence, and
   operational concerns.
7. **Create the parent-owned artifact.** Write the approved proportional brief
   or spec where the parent workflow directs. Preserve decision status and
   acceptance criteria; do not retain conversation transcript.
8. **Self-review.** Remove unfinished markers, contradictions, ambiguous terms,
   unstated actors, missing failures, untestable acceptance criteria, and
   scope that cannot fit one plan.
9. **Obtain approval.** Present the exact final artifact. Earlier agreement on
   an idea is not approval of the completed contract.
10. **Return to the parent.** The next phase is implementation planning from
    the approved design. Do not start code in the handoff.

## Scope Control

- If the request contains independent subsystems that cannot be reviewed as
  one coherent delivery, decompose it before refining implementation details.
- Hidden complexity can raise the required rigor. It never justifies silently
  lowering it.
- In an existing codebase, improve only boundaries that materially affect the
  requested outcome. Do not add unrelated refactors.
- A simplification that changes visible behavior is an approach requiring
  approval, not an implementation shortcut.

## Design Quality

For each unit, make its purpose, public interface, dependencies, failure modes,
and evidence understandable without reading its internals. Prefer existing
repository patterns and native platform behavior. Add an abstraction only when
it removes demonstrated complexity or matches an established boundary.

## Visual Companion

Offer the visual companion only when a real design question would be clearer
shown than described. The offer must be its own message and requires approval.
Use it for mockups, layout comparisons, and diagrams, not ordinary requirement
questions. When accepted, read [visual-companion.md](visual-companion.md)
before starting it.
