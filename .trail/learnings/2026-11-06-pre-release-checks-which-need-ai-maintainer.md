---
title: "Pre-release checks: which need AI and how to run them"
author: maintainer
date: 2026-11-06
branch: main
cost: { minutes: 1, tokens: 18976 }
touches:
  - docs/PLAN.md
  - memory.md
  - dev/scrub.sh
  - dev/test-install.md
---

## Decided
- Before the 0.2.0 release, no model is needed for: unit tests, `bash dev/scrub.sh`, `claude plugin validate`, the W1 listing check (local marketplace in a throwaway CLAUDE_CONFIG_DIR), the release dry run, and `dev/test-install.md` Parts 1 to 5 without step 11.
- Model use: `dev/run-evals` (about $1 for ten cases on Sonnet, run from the terminal one `--case` per run), SkillSpector on Sonnet, the Opus re-review, W0 step 11, the W1 init-command check, and W15 (walkthrough section 6 prompts in a live session).
- The maintainer runs the terminal checks and shares logs; commands pipe through `tee` so all output is kept.

## Tried and ruled out
- Treating the evals as model-free: they are real agent runs.

## Watch out
- W0 asks for `main` level with `origin/main` and nothing staged; it fails while commits are unpushed or files are staged.
- The install check at V=0.1.0 tests the pushed tag, not unpushed commits; the W1 local-marketplace check does test them.
- Scan SkillSpector on `git archive HEAD skills/pmo-docs`, not the working tree.
