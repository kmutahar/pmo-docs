---
title: Release zip and GitHub release workflow
author: maintainer
date: 2026-11-05
touches:
  - README.md
  - ".github/workflows/release.yml"
---

## Decided
- The release zip is `git archive --prefix=pmo-docs/ <tag>:skills/pmo-docs`, so end users get only the skill folder. `.github/workflows/release.yml` builds it on a `v*` tag, takes the version's section of `CHANGELOG.md` as the release notes and runs `gh release create`. It worked on its first run (v0.1.0).

## Watch out
- A zip built before `dev/release` still says version 0.0.0.
- The workflow fails if `CHANGELOG.md` has no section for the tag, so the changelog must be in the tagged commit.
