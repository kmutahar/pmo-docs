---
title: Pruning learnings before publishing
author: maintainer
date: 2026-11-07
touches:
  - AGENTS.md
---

## Decided
- Learnings are committed to a public repo, so keep only rules that outlive one task: drop agent-run logs, finished audits, personal workflow and anything naming gitignored `tmp/` files or private tooling.
- No `cost` or `branch` front matter; it is noise in a public repo.
- Delete a learning with a plain `rm`, not `git rm --cached`.

## Tried and ruled out
- Keeping learnings that only restate `docs/PLAN.md`, `AGENTS.md` or `memory.md`: they go stale and can contradict them.

## Watch out
- Check a learning's numbers against `AGENTS.md` before keeping it (one said ten evals and $1; the repo has thirteen and about $1.50 for all).
- Re-read the learnings after a change of policy: one said every commit must pass its tests alone after the maintainer chose to test at the end.
