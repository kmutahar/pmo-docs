---
title: "Check git status before reporting what's next"
author: maintainer
date: 2026-11-05
standing: true
---

## Decided
- When asked "what's next" or about the state of the work, run `git status -sb` (and `git tag`) first. Do not answer only from the project notes.

## Watch out
- The index (staged, unpushed, untracked) changes between sessions and sometimes in the middle of one, and you will not know who changed it. Report what you see.
