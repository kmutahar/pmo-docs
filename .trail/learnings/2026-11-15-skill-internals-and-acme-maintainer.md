---
title: Skill internals and the Acme fixture
author: maintainer
date: 2026-11-15
touches:
  - skills/pmo-docs/skills/
  - skills/pmo-docs/scripts/structure_check.py
  - skills/pmo-docs/scripts/render_views.py
  - skills/pmo-docs/assets/starter/bin/pmo
  - docs/walkthrough.md
  - examples/acme/pmo/registers
---

## Decided
- Command skills live in `skills/pmo-docs/skills/<name>/SKILL.md` (`disable-model-invocation: true`); fallback `commands/*.md`. Plugin `skills` paths must start with `./` and stay inside `skills/pmo-docs`, so root-level skills fail validation.
- `examples/acme` feeds the tests, evals and `docs/walkthrough.md`. After any Acme register or document change, re-run the walkthrough commands on a fresh Acme copy and paste the new output, `where.py --hashes` lines included.

## Watch out
- In a sub-skill `${CLAUDE_SKILL_DIR}` is the sub-skill's folder; use `${CLAUDE_PLUGIN_ROOT}` (substituted in skill text, not set in Bash) to reach `scripts/` and `references/`. With `disable-model-invocation` the description stays out of context and `$ARGUMENTS` works.
- `structure_check` reports every template front-matter key (except `checks`) a document lacks. An optional field must stay out of the templates, or every existing document fails.
- `pmo/bin/pmo` finds the skill only in project skill folders, the plugin cache or home skill folders. In CI set `PMO_DOCS_SKILL` after fetching the skill.
- `render_views.validate` works on parsed entries with no line numbers; positions come from the register text (one entry per line).
- Nothing checks walkthrough output, so counts and hashes drift silently. A `setup.py` project has fewer registers than Acme, so README quick-start view counts differ.
