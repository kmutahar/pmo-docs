---
title: Evals - sandbox limits and reading a failure
author: maintainer
date: 2026-11-15
touches:
  - dev/run-evals
  - evals/
---

## Decided
- Before changing `SKILL.md` for a failed eval, compare the agent's output with what the scripts print on a temp copy of `examples/acme` (for example `generate.py <type> <period> --as-of <date> --stdout`). If they match, the grader or fixture is wrong, not the skill.
- Re-run a failing case alone first: results are single samples, and split votes mostly come from a weak judge (`dev/run-evals` passes a Sonnet judge). Read the judge's reasons in `report.html`.
- A case is only as strong as its graders that can fail: list Bash graders (blocked in the sandbox) and Edit-only or Write-only graders separately.

## Tried and ruled out
- Reproducing the sandbox Bash failure (`apply-seccomp ... setgroups ... Permission denied`) from the main shell: `bwrap` works there, and `--allow-tools` and the AppArmor sysctl did not help. It belongs to the eval sandbox.
- Driving `dev/run-evals` with a fake `claude` from an agent session: the permission check refuses it.

## Watch out
- Bash fails in every eval, so evals test only the no-script fallback. A grader must not depend on Bash, and the fallback must name every file the scripts would have read.
- Agents run in `dontAsk` mode: Glob and Grep outside the cwd are denied, Read of an exact path works. A playbook step needs a full `${CLAUDE_SKILL_DIR}/...` path.
- A prompt must name the file the agent writes, pin today's date, and ask for every sentence its llm grader requires.
- A "no edit" pattern on `pmo/documents/` also matches the agent's own new draft. Graders may run `input_match` on serialised JSON, so a pattern ending in `$` can never match.
- Parallel cases hit rate limits sooner: lower `--jobs`. `claude plugin eval --keep-temp` seals the folder (mode 000): `chmod -R u+rwX` first.
