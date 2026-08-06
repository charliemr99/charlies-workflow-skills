# Hallmark Routing

Hallmark is optional visual-direction support. Select it only when it materially
helps an approved visual goal; the presence of UI alone is insufficient.

## Select Hallmark

Use Hallmark for one or more of these conditions:

- Customer-facing greenfield pages.
- Brand, marketing, portfolio, editorial, or launch surfaces.
- Explicit visual originality or high-expression acceptance criteria.
- An approved structural redesign.
- A user-provided URL or screenshot whose design DNA should be studied.
- An explicit Hallmark request.

Normally skip Hallmark for operational dashboards, admin tools, dense tables,
forms, design-system maintenance, and localized UI fixes. An explicit user
request may override this default.

## Select the Mode

| Need | Hallmark mode |
| --- | --- |
| Extract direction from an approved reference | `hallmark study` during discovery |
| Build an approved high-expression greenfield surface | Default Hallmark during implementation |
| Replace an existing visual structure | `hallmark redesign` after explicit approval |
| Find visual anti-patterns without edits | `hallmark audit` before final browser QA |

Do not let a study silently become an implementation or a redesign silently
expand file-deletion scope.

## Precedence

The following override Hallmark opinions:

1. Explicit user requirements.
2. Product behavior and information architecture.
3. Repository conventions and established brand/design systems.
4. Accessibility, compatibility, and responsive requirements.
5. Emil Design and UI/UX Pro Max findings grounded in the actual product.

Do not apply blanket Hallmark rules when they conflict with those constraints.

## Verification and Artifacts

Hallmark audit is advisory code/design input, not runtime proof. After it:

- Verify functional behavior and responsive layouts with Playwright.
- Use Emil Design and UI/UX Pro Max for interaction, accessibility, and
  responsive quality.
- Cover the normal mobile/tablet/desktop matrix for meaningful responsive work.
- Resolve or explicitly reject each material Hallmark finding before final QA.

Do not commit `.hallmark/`, generated `design.md`, Hallmark stamps, previews, or
other transient artifacts unless the user explicitly approves a canonical
destination and durable purpose. Remove unapproved artifacts before staging.
