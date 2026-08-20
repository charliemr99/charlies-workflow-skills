---
name: subagent-driven-development
description: Use to execute an approved implementation plan through fresh implementer and reviewer contexts when tasks are independently delegable.
license: MIT
compatibility: Adapted for parent workflow routers that own final review, cleanup, and publication.
---

# Subagent-Driven Development

Execute an approved plan task by task using a fresh implementer context and a
separate task-review context. This is an execution technique, not a replacement
for discovery, planning, final branch review, or publication.

## Parent Contract Integration

When selected by Charlie's Workflow, Charlie owns artifact location, approval
evidence, sequencing, exact-HEAD verification, final review, cleanup, and
publication. Apply this skill only inside Charlie's Implement phase and return
the consolidated result to Charlie's Verify and Review phases. The parent
contract wins if any bundled prompt suggests a different lifecycle.

## Use When

- an approved implementation plan exists
- task boundaries and interfaces are explicit
- tasks can be delegated without sharing mutable in-memory context
- the harness exposes isolated subagent or worker contexts

Stay inline when tasks are tightly coupled, the next step depends on exploratory
debugging, or delegation would cost more context than it saves. Lack of a
subagent capability does not block the parent workflow; execute the same plan
inline.

## Hard Gates

- Never dispatch from an unapproved or stale plan.
- Never let a worker broaden product scope or alter acceptance criteria.
- Never mark a task complete without witnessed tests and an independent task
  review.
- Never publish, clean temporary artifacts, or claim the whole branch is ready
  from a per-task result.

## Preflight

1. Record the plan path, plan digest, source-design digest, base commit, and
   global constraints.
2. Check every task for a bounded write set, explicit interfaces, test commands,
   and an independently reviewable completion signal.
3. Identify shared files. Serialize tasks that touch the same source or test
   boundary.
4. Create a progress ledger with `pending`, `implementing`, `reviewing`,
   `fixing`, or `complete` for each task. Only one writer owns a shared file
   at a time.

## Per-Task Loop

### 1. Build the task brief

Use `scripts/task-brief` or construct the same bounded package manually.
Include:

- the exact task text and global constraints
- approved design and plan digests
- base commit and allowed write paths
- interfaces produced by prior tasks
- exact RED and GREEN commands
- prohibited scope and files
- required report format

The implementer prompt is [implementer-prompt.md](implementer-prompt.md).

### 2. Dispatch one implementer

The worker must inspect relevant local context, run the planned failing test,
implement the smallest complete behavior, run the planned passing and regression
checks, inspect its diff, and report one status:

- `DONE`: task behavior and checks complete
- `DONE_WITH_CONCERNS`: complete, with a concrete residual concern
- `NEEDS_CONTEXT`: missing fact prevents correct implementation
- `BLOCKED`: reproducible external or technical blocker

The report includes changed files, RED evidence, GREEN evidence, commit(s),
deviations, and concerns. A status without evidence is incomplete.

### 3. Build an immutable review package

Record the implementer's actual task base before dispatch. Generate the package
with `scripts/review-package BASE HEAD`; never assume `HEAD~1`, because one
task may contain multiple commits. Confirm that the package covers only the
allowed write set.

### 4. Dispatch a separate task reviewer

Use [task-reviewer-prompt.md](task-reviewer-prompt.md). Review in this order:

1. approved task and acceptance-criterion compliance
2. test quality and witnessed RED/GREEN evidence
3. correctness, maintainability, security, and repository conventions
4. unnecessary abstraction or scope

The reviewer returns `APPROVED`, `CHANGES_REQUIRED`, or `BLOCKED`, with
file and line references for every actionable finding.

### 5. Close findings before moving on

For `CHANGES_REQUIRED`, return only the findings and original task context to
a fresh fix worker, rerun the affected checks, rebuild the review package, and
request another independent review. Do not waive critical or important findings
because a later task might hide them.

For `NEEDS_CONTEXT` or `BLOCKED`, resolve discoverable repository facts in
the parent session. Ask the user only when a material decision or external
action cannot be inferred safely.

### 6. Update the ledger

Mark the task complete only after approval. Record task base, task head, test
commands, review verdict, and any deferred non-blocking observation. Then start
the next dependency-ready task.

## Concurrency Rules

- Parallelize only tasks with disjoint write sets and no unmet interface
  dependency.
- One worker per task and one reviewer per immutable package.
- Reviewers do not modify code.
- A worker never reviews its own result.
- Do not dispatch multiple workers to solve the same failure.

## Final Handoff

After every task is approved, produce one package for Charlie's remaining
phases:

```text
Plan SHA-256: <digest>
Completed tasks: <ids>
Branch base: <sha>
Candidate HEAD: <sha>
Tests witnessed: <commands and outcomes>
Per-task reviews: <verdicts>
Open concerns: <none or concrete list>
```

Return control to Charlie's Verify and Document phase. Charlie performs broad
functional, code, relevancy, and simplicity review against the exact candidate
HEAD before any cleanup or draft PR.
