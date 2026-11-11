---
title: Reviewing a build against its plan
author: maintainer
date: 2026-11-07
touches:
  - skills/pmo-docs/SKILL.md
---

## Watch out
- A playbook that says "copy the values the script printed" must match the key each field expects. Check relative-path bases (project root vs `paths.documents`).
- `SKILL.md` and the playbooks written by sub-agents can contradict each other (for example "only from a finished original" against drafting from a draft original). Read both side by side.
- Agent-drafted work is untested until the tests run: a first run after a batch of packages showed failures in the new tests. Read the code against the plan, and look for tests that pass vacuously.
