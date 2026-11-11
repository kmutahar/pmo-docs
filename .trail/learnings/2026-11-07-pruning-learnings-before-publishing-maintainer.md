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
- Check a learning's numbers and names against `AGENTS.md` and the repo before keeping it (counts of evals and costs go stale fast). Prefer no number to a wrong one.
- Re-read the learnings after a change of policy or tooling: a learning that describes a replaced tool or an old way of working (an outer `xargs` loop, a deleted script) is worse than none.
- When several learnings cover one topic, merge them into one file and delete the rest; keep the front matter to `title`, `author`, `date`, `touches`.
