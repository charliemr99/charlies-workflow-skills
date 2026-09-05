# Discover and Spec

## Input

Grounded routing and valid discovery state from action 01.

## Output

Decision-complete proportional spec with recorded approval.

## Process

1. Resolve build-changing unknowns from repository evidence first. Keep decisions
   in the spec as `settled`, `open`, or `deferred`, with evidence/assumptions.
   Use `brainstorming` only when unresolved discovery needs that technique.
   `No blocking questions` requires no open blocker or major decision. Defer only
   items outside approved scope; savings or Ponytail cannot justify omissions.
2. Ask concise material questions in interactive mode. In autonomous mode, record
   bounded assumptions and proceed; human-only authority blockers still apply.
3. Write a concise spec with outcome, scope/non-goals, changed contracts and
   invariants, acceptance IDs, edge/failure behavior and proof requirements.
   Include operations/rollout only where applicable. Complex specs must cover
   all relevant risks; reference existing contracts instead of copying them.
   Keep this as the single decision source, not a parallel discovery transcript.
4. Obtain explicit user approval in interactive mode, or record the existing
   autonomous authorization. Every interactive Small brief needs approval unless
   a complete Small request already contains an explicit execution instruction
   and all required decisions; that exception belongs to the entrypoint route.
5. For Medium/Complex, hash approved spec bytes as `spec_sha256`; record
   `spec_approval_evidence`, path, status and discovery completion. A changed spec
   invalidates its plan binding; material changes require renewed approval.
   Present a short decision summary and link, not the entire spec again.

## Exit Test

No open build-changing decisions remain, the spec is approved, and approval
identity/evidence are recorded. Advance to planning; source edits remain blocked.
