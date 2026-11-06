---
title: Testing a release before it is published
author: maintainer
date: 2026-11-06
branch: main
cost: { minutes: 76, tokens: 288051 }
touches:
  - README.md
  - dev/test-install.md
  - docs/PLAN.md
  - docs/plans/v0.4.md
  - docs/plans/v0.5.md
  - docs/plans/v1.0.md
---

## Decided
- Before the tag exists, the install check runs from `dev/test-install.md` against a local marketplace (`claude plugin marketplace add <path to the clone>`, project scope, in a throwaway `CLAUDE_CONFIG_DIR`) and a zip built with `git archive --format=zip --prefix=pmo-docs/ -o <zip> HEAD:skills/pmo-docs`. Steps 1 to 10 and 14 to 20 need no model; only steps 11 to 13 (live session) need a login.
- That local run counts as the install check for the release. The version it shows is the old one, because `dev/release` writes the new version; a `V=<new>` run against the real zip is only possible after the tag is pushed.
- Expected numbers move with each release: views written by `render_views.py` (17 at v0.2) and files in the zip (83 at v0.2). Update `dev/test-install.md` when they change.
- `dev/release` reads its two prompts from the terminal, so only the maintainer runs the real release; the agent runs `--dry-run` (with `--allow-dirty` when files are staged).
- Every command block given to the maintainer saves its output to a log folder outside the throwaway folder, and cleanup is a separate block afterwards.

## Tried and ruled out
- Ending a command block with `rm -rf "$TRY"`: it deleted the transcript before anyone could share it.
- Running the check at the previous version (`V=0.1.0`) to test the new release: it tests the old tag.

## Watch out
- A text replacement that does not match changes nothing and prints no error; check the line afterwards (a plan line kept its old tail because the replacement started with a comma where the text had a semicolon).
- A local marketplace copies the working tree, so a `__pycache__` can show up in the installed scripts; the release zip comes from `git archive` and has none.
