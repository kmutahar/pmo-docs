---
title: "Commit in several chunks, in task order"
author: maintainer
date: 2026-11-05
standing: true
---

## Decided
- Split commits into reviewable chunks that follow the order of the plan's packages, one topic per commit. Propose the chunks and their subjects first.
- A correction to something unreleased is a `refactor:`, so it stays out of the changelog.
- Mark each plan package `Status: done` in the commit that completes it.
- For one big task the maintainer may let the agent restage per commit. Build each commit's version of a shared file from a pinned base commit, and compare the final tree with a saved copy of the working tree.

## Watch out
- `git commit -- <paths>` commits the whole working-tree file, so a file shared by several packages needs hunk-level staging or an earlier version staged first.
- A rebase refuses to run with staged files. To reorder unpushed commits without touching the index, use `git commit-tree`; in zsh write `${sha}:path` with braces (`$B:A` is a modifier).
