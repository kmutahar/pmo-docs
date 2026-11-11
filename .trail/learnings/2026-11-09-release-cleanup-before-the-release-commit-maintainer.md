---
title: Release cleanup before the release commit
author: maintainer
date: 2026-11-09
touches:
  - README.md
  - docs/PLAN.md
  - docs/plans/
---

## Watch out
- The cleanup commit deletes the version's plan file, and with it any unfinished checklist. Move unfinished work to the next plan or the hub first.
- The release date written in the hub row is UTC and must match the day the tag is made.
- Delete the plan with a plain `rm` and leave the deletion unstaged; `git rm --cached` stages it.
