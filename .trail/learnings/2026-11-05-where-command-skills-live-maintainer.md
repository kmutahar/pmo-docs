---
title: Where the init and publish command skills live
author: maintainer
date: 2026-11-05
touches:
  - skills/pmo-docs/skills/init/SKILL.md
  - skills/pmo-docs/skills/publish/SKILL.md
  - skills/pmo-docs/.claude-plugin/plugin.json
---

## Decided
- `skills/pmo-docs/skills/init/SKILL.md` and `skills/pmo-docs/skills/publish/SKILL.md`, both `disable-model-invocation: true` (v0.2 D8). Fallback: `skills/pmo-docs/commands/*.md`.

## Tried and ruled out
- `skills/init` and `skills/publish` at the repo root: every plugin `skills` path must start with `./` and resolve inside the plugin root, which is `skills/pmo-docs`. A `../init` path fails validation.

## Watch out
- The default `skills/` scan picks up `skills/pmo-docs/skills/<name>/` even with `"skills": ["./"]`. The docs do not say whether `./` also scans nested folders, so a skill might load twice: check with `claude plugin validate` and `/plugin` (still to check live).
- In a sub-skill, `${CLAUDE_SKILL_DIR}` is the sub-skill's own folder, not the plugin root. Use `${CLAUDE_PLUGIN_ROOT}` (substituted in skill text, not set in Bash) to reach `scripts/` and `references/`.
- Legacy `commands/*.md` takes the same front matter and is namespaced `/pmo-docs:<file>`.
- With `disable-model-invocation: true` the description stays out of context, the model cannot invoke the skill, and `$ARGUMENTS` works.
