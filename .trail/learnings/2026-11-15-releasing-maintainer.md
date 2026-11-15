---
title: Releasing - test before the tag, clean up before the release commit
author: maintainer
date: 2026-11-15
touches:
  - dev/release
  - dev/test-install.md
  - cliff.toml
  - .github/workflows/release.yml
---

## Decided
- Run the install check (`dev/test-install.md`) before the tag exists, against a local marketplace (project scope, throwaway `CLAUDE_CONFIG_DIR`) and a zip from `git archive --format=zip --prefix=pmo-docs/ -o <zip> HEAD:skills/pmo-docs`. It shows the old version, because `dev/release` writes the new one; a `V=<new>` run works only after the tag is pushed.
- Cleanup goes in its own commit before the release commit, never inside it. Release dates are UTC and must match the tag day.
- Check that a release has a changelog section by reading the written `CHANGELOG.md` (`^## \[X.Y.Z\]`), not the `git-cliff --unreleased` preview.

## Tried and ruled out
- `V=<old>` install check to test the new release: it tests the old tag.
- Install check C needs manual permission mode (the doc says so); check D runs through `claude -p`, so the mode switch does not apply to it.
- The `--unreleased` preview: with `render_always = true` it prints a version heading even when cliff.toml skips every commit, while `git-cliff -o CHANGELOG.md --tag vX` writes no section, and `release.yml` then fails after the tag is public.

## Watch out
- A release whose only new commits are chore/ci/test/refactor or docs(plan|dev|memory) has no changelog section: add a user-facing commit first.
- A local marketplace copies the working tree, so a `__pycache__` can appear in the installed scripts; the `git archive` zip has none. Scan SkillSpector on a `git archive` copy too.
- A text replacement that does not match changes nothing and prints no error: print the changed line afterwards.
