---
title: Reviewing a build against its plan
author: maintainer
date: 2026-11-07
touches:
  - skills/pmo-docs/SKILL.md
  - skills/pmo-docs/scripts/where.py
  - docs/PLAN.md
---

## Decided
- `translation_of` is relative to `paths.documents`, so `where.py --lang` prints a quoted `translation_of` line to copy into a translation's front matter, as well as `original` (relative to the project root).
- `done_on` is set for dropped tasks as well as done ones (a closed status).
- Reviews read the code and check it against the plan; the maintainer runs the tests and evals once, before the release.

## Watch out
- A playbook that says "copy the values where.py printed" must match the key each field expects. Check relative-path bases (project root vs `paths.documents`).
- `SKILL.md` and the playbooks written by sub-agents can contradict each other (e.g. "only from a finished original" vs drafting from a draft original). Read both side by side.
- Behaviour rules repeated in other playbooks should point to `SKILL.md` instead.
- Agent-drafted work is untested until the tests run; a first run after a batch of packages showed failures in the new tests.
