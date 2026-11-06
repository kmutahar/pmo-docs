---
title: "Draft with a cheaper agent, check cheaply, review once"
author: maintainer
date: 2026-11-06
touches:
  - dev/scrub.sh
  - PRIVACY.md
  - AGENTS.md
---

## Decided
- To save Claude usage, a second coding agent drafts one work package at a time; Claude only checks and reviews.
- Order: draft, then the free checks (`python3 -m unittest discover tests`, `bash dev/scrub.sh`), then Haiku on a narrow checklist (do the referenced files, packages and keys exist; glossary updated; rules only in `SKILL.md`; breaking-change subject; no new dependency; `PRIVACY.md` in step), then one Opus high review per commit, then the maintainer approves.
- Review agents write findings to a file and reply with counts only. Treat findings as leads, not facts.
- The draft agent's prompt names the spec section, the allowed commands and the forbidden git write commands, and leaves live-login steps to the maintainer.

## Tried and ruled out
- Haiku for an open-ended deep review (see the evals and scans learning).
- Letting the reviewer commit: `AGENTS.md` requires the maintainer's approval.

## Watch out
- A draft agent does not read `AGENTS.md` on its own: the prompt must point at it and name the folders it may not read.
- Never print an agent's local config: it can hold an API key.
