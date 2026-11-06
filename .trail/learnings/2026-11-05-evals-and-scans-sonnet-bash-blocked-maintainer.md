---
title: "Evals and scans: use Sonnet; Bash is blocked in the eval sandbox"
author: maintainer
date: 2026-11-05
touches:
  - dev/run-evals
  - dev/skillspector-baseline.yaml
  - AGENTS.md
---

## Decided
- Run evals on Sonnet through `dev/run-evals`, one `--case` per run. Run SkillSpector LLM scans on Sonnet too (`AGENTS.md`).

## Tried and ruled out
- Haiku for evals (fails 5 of 9 cases) and for the SkillSpector scan (false findings on the vendored PyYAML). Use it only for mechanical work.
- Plain `claude plugin eval` from the repo root: the skill never fires, because the plugin root is `skills/pmo-docs`. Use `dev/run-evals`.
- Reproducing the eval sandbox Bash failure (`apply-seccomp ... setgroups ... Permission denied`) from the main shell: `bwrap` works there, so the failure belongs to the eval sandbox. `--allow-tools` and the AppArmor sysctl `kernel.apparmor_restrict_unprivileged_userns` did not help either.

## Watch out
- Bash is blocked in the eval sandbox, so the agent cannot run the scripts there (`SKILL.md` names `assets/templates/` as the fallback for `where.py`) and graders must not depend on Bash.
- Open question (v0.2 W14): an AppArmor profile for the `claude` binary or `bwrap`, other sandbox settings, or a container. Kernel settings need sudo: ask the maintainer.
