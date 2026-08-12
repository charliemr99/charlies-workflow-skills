# Discover and Spec

## Input

- Grounded repository context, selected track and tier, and approval mode.
- The user's requested outcome and every known product or technical constraint.
- `project-track.md` when Project Track is selected.

## Output

- A decision ledger whose entries are `settled`, `open`, or `deferred`.
- A proportional, internally reviewed spec or Small-work brief.
- Recorded `spec_approval_evidence` plus a `spec_sha256` fingerprint when a
  spec file exists.

## Process

1. Load `brainstorming` / `superpowers:brainstorming` for non-trivial work.
2. Build the decision ledger around outcome, actor, pain, trigger, journey,
   visible behavior, scope, non-goals, state, inputs, APIs, permissions,
   invariants, acceptance evidence, edge cases, failure modes, dependencies,
   rollout, and rollback.
3. Mark each decision:
   - `settled`: supported by the request, repository evidence, or an approved
     answer.
   - `open`: could materially change what gets built, how it behaves, or how it
     is accepted.
   - `deferred`: intentionally postponed with impact, default, and a reason it
     does not block this delivery.
4. In interactive mode, ask one coherent chain of the highest-impact questions
   at a time. Continue until no blocker or major build-changing decision is
   `open`. Do not optimize for a question count.
5. Say `No blocking questions` only after showing the request/repository facts
   that settled the decisions and the assumptions being used. A vague request
   or an unexplained product choice is not sufficient rationale.
6. In autonomous mode, do not ask routine questions. Record conservative
   assumptions and choices in the same ledger; autonomy does not weaken the
   readiness test.
7. Present two or three viable approaches with tradeoffs when product shape or
   architecture has a meaningful choice. Recommend one.
8. When Ponytail mode is `lite`, `full`, or explicitly `ultra`, apply it only
   after the requested outcome and repository flow are understood. Record the
   highest viable simplicity rung and surface any behavior-changing reduction
   as an approach for spec approval, never as a silent scope change.
9. For Small work, present an in-conversation brief with goal, non-goals,
   affected surfaces, acceptance criteria, test cases, and browser scenarios.
   Every interactive Small brief must be presented before planning. If the
   brief adds or changes a material decision, stop for explicit approval.
   Record `not-required` only when the user's request itself already contains
   the complete brief and its explicit execution instruction is recorded as
   approval evidence. Do not infer this status from a vague request.
10. For Medium and Complex work, write the temporary spec in the ignored run
   directory. It must include context, user-visible behavior, scope/non-goals,
   contracts and invariants, acceptance criteria, edge/error cases, test and
   browser evidence, rollout concerns, and deferred decisions.
11. Scan the draft for an unstated assumption, ambiguous term, missing actor,
    edge case, failure mode, acceptance criterion, and dependency. Resolve all
    blocker and major findings before approval.
12. In interactive mode, stop for explicit user approval of the presented spec
    or Small brief unless the complete Small-request rule above applies.
    Approval of an idea or earlier answer is not approval of the presented
    contract. In autonomous mode, record `auto-approved` only because the user
    explicitly selected that mode.
13. Record `spec_approval_evidence` as the current-conversation approval or the
    explicit instruction that authorized autonomous approval. Do not infer it
    from implementation permission alone.
14. After approval, compute the file's SHA-256 digest and record it as
    `spec_sha256`. Any later spec edit invalidates approval, approval evidence,
    and every plan derived from it.

Production edits remain blocked throughout this action.

## Exit Test

- Every material decision is `settled` or safely `deferred`; no blocker or
  major item remains `open`.
- The proportional spec status is `approved`, `auto-approved`, or legitimately
  `not-required` because a complete Small request plus its explicit execution
  instruction supplied the brief and approval evidence.
- `spec_sha256` is recorded for every file-backed spec.
- `spec_approval_evidence` identifies the current-conversation approval mode.
- Any Ponytail simplification that affects behavior is settled through the
  approved spec rather than applied implicitly.
- The state advances to `planning`; production files remain untouched.
