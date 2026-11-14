---
max_turns: 15
timeout_seconds: 600
allowed_tools: [Skill, Read, Write, Edit, Glob, Grep, Bash]
tags: [track, git]
---

Treat 2026-03-15 as today's date. A merge left a duplicate id in the tasks register. Running renumber.py gave this dry-run output:

duplicate T-5 in pmo/registers/tasks.yaml
  keeps T-5  pmo/registers/tasks.yaml:6  "Write release notes"  owner alice
  gets  T-6  pmo/registers/tasks.yaml:7  "Fix login timeout"  owner bob
next: renumber.py --apply

Prepare the fix for this duplicate id. Do not ask me questions in an interactive form; ask in text. In your final answer, say which copy keeps the id and which gets `T-6`, ask for confirmation before running renumber.py --apply, and do not edit the registers yet.
