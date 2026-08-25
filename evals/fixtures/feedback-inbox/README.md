# Feedback Inbox Fixture

A deliberately small, established browser application used to evaluate agent
delivery workflows. The baseline renders feedback but has no search or status
filtering.

## Commands

```sh
corepack pnpm test
corepack pnpm lint
corepack pnpm build
corepack pnpm test:e2e
```

Workflow skills, evaluation state, and browser artifacts are ignored. The
fixture contains no credentials, backend, analytics, or deployment target.
