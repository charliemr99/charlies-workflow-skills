# Ponytail Routing

Ponytail is optional simplicity support. Charlie routes to it automatically
when it can materially reduce code or ownership cost, but Ponytail never owns
workflow sequencing, requirements, safety, or proof.

## Precedence

Apply these constraints before any Ponytail preference:

1. Explicit user requirements and approved acceptance criteria.
2. Repository and child-workflow rules.
3. Charlie's spec, approval, plan, TDD, verification, documentation, and review
   gates.
4. Correctness, security, privacy, accessibility, compatibility, financial
   precision, and data-loss prevention.
5. Ponytail's preference for the smallest complete solution.

Ponytail may reduce implementation complexity. It may not remove required
behavior, evidence, safety checks, or the final Charlie report.

## Automatic Selection

For coding work, `ponytail_routing` defaults to `auto`. After repository
grounding, select and record one mode plus concrete `ponytail_reason` evidence:

| Mode | Select when |
| --- | --- |
| `off` | No code changes are planned, the edit is generated or mechanical, or no meaningful simplification signal exists |
| `lite` | A simpler alternative is plausible but risk, compatibility, or established architecture makes imposing it premature |
| `full` | Evidence clearly favors reuse, standard-library or native behavior, an installed dependency, a shared root-cause fix, or removal of speculative structure |
| `unavailable` | Ponytail is relevant but the current harness cannot load it |

Do not ask a separate Ponytail mode question. Announce the automatic decision
with the other Ground and Route results; the user can override it before
approving the spec.

Automatic signals include:

- a proposed new dependency;
- a new helper, wrapper, factory, interface, configuration layer, or extension
  point;
- similar behavior already present in the repository;
- a standard-library, browser, platform, database, or installed-dependency
  alternative;
- a bug symptom that may share one root call path;
- speculative flexibility, scaffolding, or future-proofing;
- a refactor whose requested outcome includes simplification.

Honor an explicit `no ponytail`, `stop ponytail`, or `normal mode` request as
`off`. Honor explicit `lite`, `full`, or `ultra` selection. Never select `ultra` automatically; it requires an explicit user request.

When available, accept local and plugin-qualified names:

- `ponytail` / `ponytail:ponytail`
- `ponytail-review` / `ponytail:ponytail-review`
- `ponytail-audit` / `ponytail:ponytail-audit`

Do not hardcode a versioned machine-local plugin path. If the helper is
unavailable, preserve Charlie's normal scope and relevancy review, record the
gap, and continue; optional Ponytail availability is not a publication blocker.
When `lite`, `full`, or explicit `ultra` is selected, invoke Ponytail with that
exact mode instead of relying on its default intensity.

## Phase Hooks

### Discover and Spec

Use Ponytail only after understanding the requested outcome and tracing the
relevant repository flow. Identify the highest simplicity rung that holds and
challenge speculative scope. Any proposal that changes requested behavior is
an explicit alternative decided through the spec approval gate, never a quiet
scope reduction.

### Plan

For each task that may add a dependency, abstraction, or new ownership surface,
include a concise `simplicity proof`:

- what existing code was searched;
- the first viable rung: reuse, standard library, native platform, installed
  dependency, one-line behavior, or minimum custom code;
- why a lower-ownership option is insufficient when custom structure remains.

Do not add this ceremony to trivial tasks with no real design choice.

### Implement

Apply the selected mode after tracing callers and ownership boundaries. Prefer
one shared root-cause fix over repeated symptom patches and implement the
smallest complete behavior that satisfies the approved acceptance criteria.
Ponytail does not replace Charlie's RED/GREEN evidence or planned regression
coverage.

## Automatic Simplicity Review

Run `ponytail-review` against the exact candidate diff when either condition is
true:

- Ponytail was active during discovery, planning, or implementation; or
- the final diff itself adds dependencies, abstraction, configuration,
  duplication, wrappers, or structure disproportionate to the behavior.

Treat it as focused input to Charlie's `relevancy` axis, not as another review
phase and not as correctness, security, or performance review. Reproduce and
assess every finding:

- a valid in-scope finding produces `iterate` until addressed and reverified;
- an invalid or constraint-conflicting finding is dispositioned with evidence;
- `Lean already. Ship.` records a clean simplicity review but cannot override a
  failure on another review axis;
- `net: -N lines possible` is informative, never an acceptance target.

Record `simplicity_review_status` as `not-selected`, `lean`,
`findings-addressed`, or `unavailable`.

## Ponytail Audit Boundary

`ponytail-audit` is repo-wide and read-only. Route to it automatically only
when the user's requested task is itself a whole-repository over-engineering or
bloat audit. During an ordinary feature, fix, or milestone, do not scan the
whole repository or import unrelated findings into the PR. Recommend a
separate audit when evidence suggests systemic debt.

If the user explicitly includes a repo-wide audit in delivery work, run it as
discovery input. Only user-selected findings that enter the approved spec may
be implemented; the remaining report stays advisory and out of scope.

## Reporting

The final report includes the selected mode and reason, whether automatic
review ran, its disposition, and an unavailable helper when relevant. Do not
let Ponytail's terse-output preference replace Charlie's required report.
