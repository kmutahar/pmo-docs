---
title: "Eval sandbox: Bash fails there, not in the main shell"
author: maintainer
date: 2026-11-05
touches:
  - dev/run-evals
---

## Tried and ruled out
- Reproducing the eval sandbox Bash failure (`apply-seccomp ... setgroups ... Permission denied`) from the main shell: `bwrap` works there, so the failure belongs to the eval sandbox. `--allow-tools` and the AppArmor sysctl `kernel.apparmor_restrict_unprivileged_userns` did not help either.

## Watch out
- An eval agent cannot run the scripts, so a grader must not depend on Bash, and a prompt must name the file the agent writes (an agent may pick its own name, such as a month prefix).
