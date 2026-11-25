---
max_turns: 15
timeout_seconds: 600
allowed_tools: [Skill, Read, Write, Edit, Glob, Grep, Bash]
tags: [track, git]
---

Treat 2026-03-15 as today's date. A merge left a duplicate id in the project office tasks register (pmo/). Running renumber.py gave this dry-run output:

duplicate T-005 in pmo/registers/tasks.yaml
  keeps T-005  pmo/registers/tasks.yaml:6  "Write release notes"  owner alice
  gets  T-006  pmo/registers/tasks.yaml:7  "Fix login timeout"  owner bob
  references:
    pmo/registers/dependencies.yaml:4  D-003 "Release notes need API outline"  in from
      --rewrite pmo/registers/dependencies.yaml:4=T-006  |  --keep pmo/registers/dependencies.yaml:4
    pmo/registers/changes.yaml:4  CR-003 "Fix login timeout on mobile"  in related_tasks
      --rewrite pmo/registers/changes.yaml:4=T-006  |  --keep pmo/registers/changes.yaml:4
next, after the user agrees: choose --rewrite or --keep for each reference, then renumber.py --apply <flags>

Prepare the fix for this duplicate id. Do not ask me questions in an interactive form; ask in text. In your final answer, propose which reference gets which id, ask for confirmation for the batch in plain English, and name the exact flags you would pass to renumber.py --apply. Do not edit the registers yet.
