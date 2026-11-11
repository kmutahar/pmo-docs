---
title: Front matter keys and the launcher outside a dev machine
author: maintainer
date: 2026-11-11
touches:
  - skills/pmo-docs/scripts/structure_check.py
  - skills/pmo-docs/assets/starter/bin/pmo
  - skills/pmo-docs/scripts/render_views.py
---

## Watch out
- `structure_check` reports every template front-matter key (except `checks`) that a document lacks, and ignores extra keys. An optional field such as `editor` must stay out of the templates, or every existing document fails.
- `pmo/bin/pmo` finds the skill only in project skill folders, the Claude plugin cache or home skill folders. In CI none exist, so a workflow must fetch the skill and set `PMO_DOCS_SKILL`. The README's pinned `refs/tags/vX.tar.gz` link is already rewritten by `dev/release`.
- The duplicate-id error in `render_views.validate` works on parsed entries, which carry no line numbers. Positions must come from the register text (one entry per line).
