# Helper Loading

## Purpose

Charlie selects helper skills deliberately and only in the phase that owns
their technique. Harness discovery and invocation syntax vary, so helper
loading cannot depend on one product-specific command.

## Resolution Order

1. Prefer the harness's native skill inventory or invocation mechanism when it
   exposes the selected helper.
2. In this package, resolve the helper as a **bundled sibling** at
   `../<helper-name>/SKILL.md` relative to Charlie's skill root.
3. For namespaced plugin skills such as `superpowers:brainstorming`, use the
   plugin-provided skill when it is available and compatible.
4. If neither the declared bundled helper nor an accepted plugin form exists,
   record it as unavailable and follow Charlie's base phase contract directly.
   Do not silently substitute an unrelated skill.

Read only the selected helper's `SKILL.md` and the resources that helper asks
for in the current phase. Loading a helper does not transfer track, approval,
artifact, review, cleanup, publication, or irreversible-action ownership away
from Charlie.
