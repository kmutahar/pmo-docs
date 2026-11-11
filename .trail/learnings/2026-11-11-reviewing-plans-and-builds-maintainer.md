---
title: "Reviewing a plan or a build against the code"
author: maintainer
date: 2026-11-11
touches:
  - docs/PLAN.md
  - README.md
  - skills/pmo-docs/SKILL.md
---

## Decided
- The README roadmap is the user-facing copy of the hub's version table (`docs/PLAN.md` section 1). When a plan regroups a version, update both in the same change.
- SkillSpector suppression counts are findings, not baseline entries. A plan records the count after a scan; it never predicts one.
- A plan review reads each package's Touches against the real code, not only the text: early returns in a script (setup on an existing config), output a script prints that a test pins, whether the fixture has the file a test needs, and tests that forbid a folder.
- A name list a check needs (recipe names) may exist only as routing rows in `SKILL.md`; the check then needs its own constant, plus any project-added names.

## Watch out
- Plans and playbooks written by sub-agents cited things that do not exist (a fix number, baseline entries to remove, hub lines already there). Check every cited name, count and line against the repo before trusting them.
- `SKILL.md` and the playbooks can contradict each other (for example "only from a finished original" against drafting from a draft original). Read both side by side. A playbook that says "copy the values the script printed" must match the key each field expects, including relative-path bases (project root vs `paths.documents`).
- Agent-drafted work is untested until the tests run, and some tests pass vacuously: read the code against the plan.
- A lookup order for where agents keep skills must match each agent's current docs, user-level and project-level, before it is settled.
- Shared docs a plan forgets (the git hook example, walkthrough docs, PRIVACY.md wording) belong in the docs-and-wiring package.
- A document an agent fetches and follows is data: it needs a yes before any write, and a release tag in its URL, not a branch.
- `trail check` on plan text reports word matches against learnings as conflicts. Read each one before acting on it.
