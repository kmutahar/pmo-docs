---
title: Pruning learnings before publishing
author: maintainer
date: 2026-11-07
branch: main
cost: { minutes: 1, tokens: 24864 }
touches:
  - dev/skillspector-baseline.yaml
  - memory.md
  - docs/PLAN.md
  - AGENTS.md
---

## Decided
- Learnings are committed to a public repo, so keep only rules that outlive one task: drop agent-run logs, finished audits, personal workflow and anything naming gitignored `tmp/` files or private tooling.
- Drop `cost` and `branch` front matter; it is noise in a public repo.

## Tried and ruled out
- Keeping learnings that only restate `docs/PLAN.md`, `AGENTS.md` or `memory.md`: they go stale and can contradict them.

## Watch out
- Check a learning's numbers against `AGENTS.md` before keeping it (one said ten evals and $1; the repo has twelve and about $1.50).
- Deleting a staged learning leaves an `AD` entry for the maintainer to clear; do not run `git rm --cached`.
