---
title: "Doc review of the plans, hub and README"
author: maintainer
date: 2026-11-06
touches:
  - README.md
  - docs/PLAN.md
---

## Decided
- The README roadmap is the user-facing copy of the hub's version table (`docs/PLAN.md` section 1). When a plan regroups a version, update both in the same change.
- SkillSpector suppression counts are findings, not baseline entries. Plans record the count after a scan; they do not predict a number.

## Watch out
- Plans written by sub-agents cited things that do not exist (a fix number, baseline entries to remove, hub lines that were already there). Check every cited name, count and line against the repo before trusting a plan.
- `trail check` on plan text reports word matches against learnings as conflicts. Read each one before acting on it.
