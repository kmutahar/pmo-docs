---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Write, Edit, Glob, Grep, Bash]
tags: [translate, glossary]
---

Translate the decision log into French. Treat 2026-03-16 as today's date. Do not ask me anything in an interactive form; reply in text. Save the translation as `pmo/documents/Decision log.fr.md`, as a draft, and write any new glossary terms to `pmo/data/glossary-fr.proposed.md`. In your final answer, quote the draft's `title` line, its `#` heading, the heading of its last section, and the table row of DEC-1 in its Summary table. Say which terms you added to a proposed glossary and in which file, and whether the original or the approved glossary changed.
