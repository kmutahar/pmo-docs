---
title: "Doc review of the plans, hub and README"
author: maintainer
date: 2026-11-06
touches:
  - PRIVACY.md
  - README.md
  - docs/PLAN.md
---

## Decided
- The README roadmap is the user-facing copy of the hub's version table (`docs/PLAN.md` section 1). When a plan regroups a version, update both in the same change.
- SkillSpector suppression counts are findings, not baseline entries (6 entries gave 9 suppressions in v0.1). Plans record the count after a scan; they do not predict an exact number.
- `PRIVACY.md` says the scripts stay inside the project and read no environment variables. Any package that reads or writes outside the project (`release-notes --repo`, publish `repo` mode, the v0.5 launcher) updates `PRIVACY.md` in its docs package.

## Watch out
- Plans written by sub-agents cited things that do not exist ("v0.1 fix 17", four baseline entries to remove, hub lines to add that were already there). Check every cited name, count and line against the repo before trusting a plan.
- `trail check` on plan text reports word matches against learnings as conflicts. Read each one before acting on it.
