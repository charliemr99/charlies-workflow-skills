# Third-Party Notices

This repository vendors skills from multiple sources. Repo-owned packaging files are MIT licensed under `LICENSE`. Vendored third-party content remains under its original license.

## OpenAI Skill Validator

The repository includes the OpenAI `skill-creator` `quick_validate.py` script,
pinned to `openai/skills` commit
`49f948faa9258a0c61caceaf225e179651397431`. It is licensed under the Apache
License 2.0. The complete license and provenance are in
`scripts/vendor/openai-skill-creator/`.

Normal validation also downloads the Agent Skills reference validator at the
pinned PyPI requirement `skills-ref==0.1.1` through `uvx`. That package is a
validation-time dependency and is not redistributed in this repository.

## Hallmark

Vendored skill:

- `hallmark`

Source:

- Repository: `Nutlope/hallmark`
- Path: `skills/hallmark`
- Version: `1.1.0`
- Reviewed commit: `aeb42fb354ff4efa36ab475773a082315a3af2ce`

The full license is preserved in `skills/hallmark/LICENSE.txt`.

Packaging modification:

- Moved upstream's top-level `version` frontmatter field to
  `metadata.version` for compatibility with the official Agent Skills
  validator.
- Added Codex `agents/openai.yaml` metadata so the optional skill remains
  explicit-only unless Charlie's Workflow selects it.
- Replaced links that escaped into omitted upstream `site/` and `docs/`
  content with URLs pinned to the reviewed commit. Those optional examples
  require network access.
- Removed one trailing blank line so the vendored tree passes `git diff
  --check`.

```text
MIT License

Copyright (c) 2026 Hallmark contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Emil Kowalski Design Engineering Skill

Vendored skill: `emil-design-eng`

Source:

- Repository: `emilkowalski/skills`
- Reviewed commit: `f76beceb7d3fc8c43309cefad5a095a206103a4e`

The skill body and MIT license are pinned to that reviewed revision. The skill
blob is unchanged from the earlier reviewed content commit
`ecf66bbd1fb33c25332b6b0e454d08049978284c`. The license is preserved in
`skills/emil-design-eng/LICENSE.txt`.

Copyright (c) 2026 Emil Kowalski.

## UI/UX Pro Max

Vendored skill: `ui-ux-pro-max`

Source:

- Repository: `nextlevelbuilder/ui-ux-pro-max-skill`
- Reviewed commit: `87c6c3e0e1a8891d79795d3e3061f10b650de51b`

Packaging modifications:

- Replaced upstream installation symlinks with the real `data/` and
  `scripts/` trees from the same reviewed commit.
- Normalized command examples to resolve from the installed skill root.
- Normalized vendored text resources from CRLF to LF and removed trailing
  line-end whitespace so repository integrity checks remain deterministic.
- Added strict Agent Skills license metadata.

The MIT license is preserved in `skills/ui-ux-pro-max/LICENSE.txt`.

Copyright (c) 2024 Next Level Builder.

## Doc It

Vendored skill: `doc-it`

Source:

- Repository: `onlydole/overdue`
- Path: `.claude/skills/doc-it/SKILL.md`
- Reviewed commit: `eb1f11807296ae09826fbfc4ecac84bda97982d9`

Packaging modifications:

- Removed Claude-only invocation metadata from the strict Agent Skills source.
- Converted `allowed-tools` from a YAML list to the Agent Skills
  space-delimited string form.
- Added license metadata.

The MIT license is preserved in `skills/doc-it/LICENSE.txt`.

Copyright (c) 2026 Taylor Dolezal.

## Superpowers

Vendored skills:

- `brainstorming`
- `writing-plans`
- `test-driven-development`
- `using-git-worktrees`
- `subagent-driven-development`

Source package: Superpowers `6.1.1`

Packaging modifications:

- Adapted brainstorming, writing-plans, and subagent-driven-development as
  phase techniques under Charlie's parent lifecycle contract.
- Removed helper-owned artifact paths, approval handoffs, final review, cleanup,
  and publication instructions that competed with the parent router.
- Omitted `executing-plans` because the parent already owns inline execution
  and the helper would require additional unbundled Superpowers siblings.

License:

```text
MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Playwright Skills

Vendored skills:

- `playwright`
- `playwright-interactive`

The `playwright` skill includes material derived from the Microsoft `playwright-cli` repository.

Source:

- Repository: `microsoft/playwright-cli`
- Reviewed commit: `34bf2ada4d4a28723bd65ba4e56ba724fdaaa959`
- Path: `skills/playwright-cli/SKILL.md`

This was the latest upstream revision for that path when the skills were first
vendored into this package on 2026-07-09.

Copyright (c) Microsoft Corporation.

Licensed under the Apache License, Version 2.0. The full license is preserved in:

- `skills/playwright/LICENSE.txt`
- `skills/playwright-interactive/LICENSE.txt`

Original notice from `skills/playwright/NOTICE.txt`:

```text
This skill includes material derived from the Microsoft playwright-cli repository.

Source:
- Repository: microsoft/playwright-cli
- Path: skills/playwright-cli/SKILL.md

Copyright (c) Microsoft Corporation.

Licensed under the Apache License, Version 2.0.
See LICENSE.txt in this directory.

Modifications:
- Adapted for the Codex skill collection.
- Added a wrapper script and local reference guides.
```

Original notice from `skills/playwright-interactive/NOTICE.txt`:

```text
This skill reuses the Playwright icon assets from `.codex/skills/playwright/assets/`.

The local `playwright` skill attributes those assets to the Microsoft
`playwright-cli` repository.

Copyright (c) Microsoft Corporation.

Licensed under the Apache License, Version 2.0.
See LICENSE.txt in this directory.

Modifications:
- Repackaged the existing repository Playwright assets for this `js_repl`-focused skill.
- Wrote new skill instructions for persistent browser debugging.
```
