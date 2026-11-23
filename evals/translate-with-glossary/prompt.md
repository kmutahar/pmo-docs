---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Write, Edit, Glob, Grep, Bash]
tags: [translate, glossary]
---

Translate the decision log into French. Treat 2026-03-16 as today's date. Do not ask me anything in an interactive form; reply in text. Save the translation as `pmo/documents/Decision log.fr.md`, as a draft, and add any new glossary terms to the Proposed section of `pmo/data/glossary-fr.md`. In your final answer, quote the draft's `title` line, its `#` heading, the heading of its last section, and the table row of DEC-001 in its Summary table. Say which terms you added to a proposed glossary and and whether the original or the Approved section changed.
