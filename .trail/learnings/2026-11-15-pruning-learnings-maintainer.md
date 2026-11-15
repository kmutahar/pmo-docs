---
title: Pruning learnings before publishing
author: maintainer
date: 2026-11-15
touches:
  - AGENTS.md
---

## Decided
- Learnings are committed to a public repo: keep only rules that outlive one task. Drop agent-run logs, finished audits, personal workflow and anything naming gitignored `tmp/` files or private tooling.
- Front matter is `title`, `author`, `date`, `touches` only. When several learnings cover one topic, merge them into one and delete the rest. Delete with plain `rm`, never `git rm --cached`.

## Tried and ruled out
- Keeping learnings that only restate `docs/PLAN.md`, `AGENTS.md` or `memory.md`: they go stale and can contradict them.

## Watch out
- Check numbers and names against the repo before keeping a learning (for example, a claim about what `dev/scrub.sh` catches went stale). Prefer no number to a wrong one.
- Re-read learnings after a policy or tooling change: one describing a replaced tool is worse than none.
