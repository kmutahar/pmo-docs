---
title: Committing in chunks and the scrub gate
author: maintainer
date: 2026-11-15
touches:
  - dev/scrub.sh
  - .githooks/pre-commit
  - .githooks/commit-msg
---

## Decided
- Commit chunks follow the plan's package order, one topic each; propose them first. A correction to something unreleased is a `refactor:` so it stays out of the changelog.
- The pre-commit hook is the real privacy gate. Under `git commit -- <paths>` git gives it a temporary index with the working-tree copies, and `scrub.sh` scans that.
- Any pipe over `pmo/` in a script or checklist uses `find ... -print0 | sort -z | xargs -0`: Acme file names hold spaces.

## Tried and ruled out
- `bash dev/scrub.sh` by hand before `git commit -- <paths>`: it scans the real index plus untracked files, so an unstaged private line in a named path reads as clean.

## Watch out
- `git commit -- <paths>` commits the whole working-tree file, so a file shared by several packages needs hunk-level staging or an earlier version staged first.
- A rebase refuses to run with staged files. To reorder unpushed commits without touching the index use `git commit-tree`; in zsh write `${sha}:path` (`$B:A` is a modifier).
- The commit-msg hook pipes the message (comment lines stripped) through `dev/scrub.sh --message -`, so subjects get the same checks as files.
- `scrub.sh` scans the index, so a staged older copy of a file is what it reports. Its machine-path rule matches a `home` folder plus a letter anywhere, including a sandbox's sealed home path: name such paths in words.
- A test file holding a path or phone sample fails the scrub: build samples from parts.
- With `2>&1` into a snapshot file, a broken step writes the same errors before and after, so a diff looks clean.
