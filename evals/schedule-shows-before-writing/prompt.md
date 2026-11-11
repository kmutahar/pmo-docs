---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Write, Edit, Glob, Grep, Bash]
tags: [schedule]
---

Schedule the weekly-status recipe to run every Monday at 08:00. Treat 2026-03-16 as today's date. Do not ask me anything in an interactive form; reply in text, and stop where the playbook says to wait for my yes. In your reply, quote the exact entry you plan to add under `schedule:` in the project's config and the exact cron line I should install myself.
