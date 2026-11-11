---
title: "Evals: sandbox limits and how to read a failure"
author: maintainer
date: 2026-11-11
touches:
  - dev/run-evals
  - evals/
---

## Decided
- Before changing `SKILL.md` for a failed eval, compare the agent's output with what the scripts print on a temp copy of `examples/acme` (for example `generate.py <type> <period> --as-of <date> --stdout`). If they match, the grader or the fixture is wrong, not the skill.
- Re-run a failing case alone first: results are single samples. Split votes (2-1) mostly come from a Haiku judge, which is why `dev/run-evals` passes a Sonnet judge.
- Read the judge's reasons in each case's `report.html`, not only the votes in the log.

## Tried and ruled out
- Reproducing the sandbox Bash failure (`apply-seccomp ... setgroups ... Permission denied`) from the main shell: `bwrap` works there, and `--allow-tools` and the AppArmor sysctl `kernel.apparmor_restrict_unprivileged_userns` did not help. The failure belongs to the eval sandbox.
- An outer `xargs` loop over cases, and killing the heartbeat loop with `kill` (its `sleep` child keeps the output pipe open for up to 30 s): `dev/run-evals` now runs cases in parallel itself and stops the heartbeat with a stop file.

## Watch out
- Bash fails in every eval, so evals test only the no-script fallback. A grader must not depend on Bash, and the fallback must name every file the scripts would have read (for example the defaults in `assets/config.default.yaml`).
- Eval agents run in `dontAsk` mode: Glob and Grep on the skill folder (outside the cwd) are denied, but Read of an exact path works. A playbook step that says "look in the skill's X" without a full `${CLAUDE_SKILL_DIR}/...` path fails there: the agent guesses or skips the step.
- A prompt must name the file the agent writes (an agent may pick its own name, such as a month prefix) and pin today's date ("Treat <date> as today's date"); without it answers drift with the real clock.
- Parallel cases are several Claude sessions at once and hit rate limits sooner: use `--jobs 2`.
- `claude plugin eval --keep-temp` seals the kept folder (mode 000 inside): `chmod -R u+rwX` before moving it.
- `dev/scrub.sh` scans the index, not the files on disk, so a staged older copy of a file is what it reports. Its machine-path rule matches a `home` folder followed by a letter anywhere, including the eval sandbox's own sealed home path, so name such paths in words, not literally.
