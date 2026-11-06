---
title: "Commit in several chunks, in task order"
author: maintainer
date: 2026-11-05
standing: true
---

## Decided
- Split commits into reviewable chunks that follow the order of the plan's packages, one topic per commit. Never one big commit. Propose the chunks and their subjects first.
- Subjects are conventional (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). A correction to something unreleased is a `refactor:`, so it stays out of the changelog.
- The maintainer normally stages and the agent runs `git commit -- <paths>`. For one big task the maintainer may unstage everything and let the agent restage per commit. Then: build each commit's version of a shared file, stage it, export the index (`git checkout-index -a --prefix=<dir>/`), run the unit tests there, and only then commit. Every commit must pass its tests alone.
- Mark each plan package `Status: done` in the commit that completes it.
- Pushing needs the maintainer's explicit OK each time.

## Watch out
- `git commit -- <paths>` commits the whole working-tree file, so a file shared by several packages needs hunk-level staging or an earlier version staged first.
- A rebase refuses to run with staged files. To reorder unpushed commits without touching the index, use `git commit-tree`; in zsh write `${sha}:path` with braces (`$B:A` is a modifier).
