# Helper Loading

## Purpose

Charlie selects helper skills deliberately and only in the phase that owns
their technique. Harness discovery and invocation syntax vary, so helper
loading cannot depend on one product-specific command.

## Resolution Order

1. In this package, resolve a declared helper as the authoritative **bundled sibling** at
   `../<helper-name>/SKILL.md` relative to Charlie's skill root.
2. Use the harness's native skill inventory or invocation mechanism only when
   it resolves that same bundled sibling and adapted contract.
3. A namespaced plugin skill such as `superpowers:brainstorming` is a fallback
   only when the bundled sibling is absent and the plugin exposes a
   compatible parent contract that preserves Charlie's ownership. Otherwise
   skip the plugin and apply Charlie's phase directly.
4. If neither the declared bundled helper nor an accepted plugin form exists,
   record it as unavailable and follow Charlie's base phase contract directly.
   Do not silently substitute an unrelated skill.

Read only the selected helper's `SKILL.md` and the resources that helper asks
for in the current phase. Loading a helper does not transfer track, approval,
artifact, review, cleanup, publication, or irreversible-action ownership away
from Charlie.
