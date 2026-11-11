---
title: "Releasing: test before the tag, clean up before the release commit"
author: maintainer
date: 2026-11-11
touches:
  - dev/release
  - dev/test-install.md
  - docs/PLAN.md
---

## Decided
- Before the tag exists, run the install check (`dev/test-install.md`) against a local marketplace (`claude plugin marketplace add <path to the clone>`, project scope, in a throwaway `CLAUDE_CONFIG_DIR`) and a zip made with `git archive --format=zip --prefix=pmo-docs/ -o <zip> HEAD:skills/pmo-docs`. Only the live-session steps need a login. That run shows the old version, because `dev/release` writes the new one; a `V=<new>` run against the real zip is possible only after the tag is pushed.
- Unit tests, `bash dev/scrub.sh`, `claude plugin validate`, the release dry run and the install check without its live-session steps need no model.
- `dev/release` reads its prompts from the terminal, so only the maintainer runs the real release; an agent runs `--dry-run`.
- Cleanup goes in its own commit before the release commit: delete the version's plan file, point the hub row to the new tag, mark the README roadmap and hub index released. Move unfinished work to the next plan or the hub first, because the plan's checklist goes with the file. The release date in the hub row is UTC and must match the day the tag is made.

## Tried and ruled out
- Running the install check at the previous version (`V=<old>`) to test the new release: it tests the old tag.

## Watch out
- A text replacement that does not match changes nothing and prints no error: print the changed line afterwards.
- A local marketplace copies the working tree, so a `__pycache__` can show up in the installed scripts. The release zip comes from `git archive` and has none. Scan SkillSpector on a `git archive` copy for the same reason.
- The release prerequisites need `main` level with `origin/main` and nothing staged; they fail while commits are unpushed or files are staged (`--allow-dirty` skips the staged check for a dry run).
- Delete a plan file with a plain `rm` and leave the deletion unstaged; `git rm --cached` stages it.
