---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Write, Edit, Glob, Grep, Bash]
tags: [extend, config]
---

I want every task in this project to carry a `reviewer` field that holds a person's slug from the roster. Set that up for this project without changing the skill itself. Treat 2026-03-16 as today's date. Do not ask me anything in an interactive form; reply in text. If you need my yes before writing, show the change and stop there. In your final answer, quote the exact `registers.tasks.fields` list that the project's `pmo/config.yaml` will hold and the file you change.
