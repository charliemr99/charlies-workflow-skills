# Verify and Document

## Input

- The source-final candidate diff and implementation verification ledger.
- Planned unit, integration, browser, responsive, and documentation evidence.
- Acceptance criteria from the approved spec or brief.

## Output

- Fresh verification evidence for the candidate tree.
- Browser artifacts for each meaningful scenario and responsive state.
- Canonical documentation status and a clean publication diff.

## Process

Before the documentation and cleanup steps, read
[`documentation-and-artifacts.md`](../references/documentation-and-artifacts.md)
and apply its Durable Documentation, Decision Promotion, and Temporary Workflow
Artifact gates. Do not preload that reference during earlier actions.

1. Stabilize the diff before broad checks. Record the candidate commit or tree
   identity so later source changes can invalidate affected evidence.
2. Run the planned focused, integration, static, build, and regression commands
   against the final candidate. Record exact commands and results.
3. For browser-relevant work, use one browser session efficiently but keep two
   distinct gates:
   - **Functional browser QA:** execute each planned user journey, recording
     action, expected result, actual result, pass/fail, downstream impact, and
     screenshot/video/log artifact.
   - **Verify Beyond the Obvious:** perform a separate UI/UX quality review of
     the source-final behavior.
4. Meaningful UI must be inspected at a minimum of three representative sizes:
   `small mobile` (for example 390x844), `tablet` (768x1024), and `desktop`
   (1440x900). Capture a screenshot for each size and important state.
5. For Verify Beyond the Obvious, load both `emil-design-eng` and
   `ui-ux-pro-max`. Review overflow, density, text fit, hierarchy, interaction,
   focus/keyboard behavior, accessibility basics, loading/empty/error states,
   supported themes, motion, and reduced-motion behavior. Functional success
   does not imply visual or interaction quality.
6. Treat every discovered defect as a new implementation loop: add or update a
   regression test when feasible, fix it, rerun invalidated checks, and repeat
   both browser gates where affected.
7. Run `doc-it` as a targeted documentation gate under
   `references/documentation-and-artifacts.md`. Record exactly one status:
   `changed`, `current`, `not-needed`, or `declined-with-gap`.
8. Promote only durable, source-final behavior and non-obvious lasting
   decisions into canonical repository documentation. Do not preserve question
   transcripts, approval logs, TDD narration, or file-by-file execution plans.
9. Delete the implementation plan and, by default, the working spec after
   durable decisions are promoted. Remove all run state and temporary evidence
   not intentionally retained as useful output. Ensure no workflow artifact or
   `docs/superpowers/` file exists in the branch history unless explicitly
   requested as canonical documentation.

## Exit Test

- All planned checks pass on the source-final candidate, or an exact external
  blocker is reported without claiming completion.
- Browser-relevant work passed functional QA; meaningful UI also passed Verify
  Beyond the Obvious at small mobile, tablet, and desktop with linked artifacts.
- Documentation has one final status and durable decisions are current.
- Temporary workflow artifacts are absent from the working tree, staged diff,
  and branch history.
- The state advances through `documenting` to `reviewing`.
