---
title: Testing a release before it is published
author: maintainer
date: 2026-11-06
touches:
  - README.md
  - dev/test-install.md
  - dev/scrub.sh
---

## Decided
- Before the tag exists, run the install check from `dev/test-install.md` against a local marketplace (`claude plugin marketplace add <path to the clone>`, project scope, in a throwaway `CLAUDE_CONFIG_DIR`) and a zip built with `git archive --format=zip --prefix=pmo-docs/ -o <zip> HEAD:skills/pmo-docs`. Only the live-session steps need a login.
- That local run counts as the install check for the release. It shows the old version, because `dev/release` writes the new one; a `V=<new>` run against the real zip is only possible after the tag is pushed.
- Expected numbers (views written by `render_views.py`, files in the zip) move with each release. Update `dev/test-install.md` when they change.
- No model is needed for: unit tests, `bash dev/scrub.sh`, `claude plugin validate`, the release dry run, and the install check without its live-session steps. Models are needed for `dev/run-evals`, the SkillSpector LLM pass and the walkthrough prompts. The evals are real agent runs.
- `dev/release` reads its prompts from the terminal, so only the maintainer runs the real release; an agent runs `--dry-run` (with `--allow-dirty` when files are staged).

## Tried and ruled out
- Running the install check at the previous version (`V=<old>`) to test the new release: it tests the old tag.

## Watch out
- A text replacement that does not match changes nothing and prints no error; check the changed line afterwards.
- A local marketplace copies the working tree, so a `__pycache__` can show up in the installed scripts; the release zip comes from `git archive` and has none. Scan SkillSpector on a `git archive` copy for the same reason.
- The release prerequisites ask for `main` level with `origin/main` and nothing staged; they fail while commits are unpushed or files are staged.
