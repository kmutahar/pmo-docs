---
title: Release cleanup before the release commit
author: maintainer
date: 2026-11-09
touches:
  - README.md
  - docs/PLAN.md
  - docs/plans/
---

## Decided
- Cleanup is its own commit before `dev/release`: delete the version plan file, point the hub row to the new tag, mark the README roadmap released, and move unfinished work to the next plan (a W0 checklist line or its section 6).
- A task that needs no agent work, such as the source project decision, moves to the next plan's W0 and the hub text is reworded so it names no deleted plan.

## Tried and ruled out
- Deleting a tracked file with `git rm --cached`: it stages the deletion, which the no-staging rule forbids. Use a plain `rm` and leave the deletion unstaged.

## Watch out
- Deleting the plan also deletes its unfinished checklist (evals, SkillSpector scan). Run them before `dev/release`, since the files already say released.
- The release date written in the hub row is UTC and must match the day the tag is made.
