---
type: llm
weight: 3
---

The project's own playbook replaces the skill's: it asks for exactly two next steps, each on its own line starting "NEXT:", the first naming Sam Example, and for a reply whose last line is "Escalation: Sam Example". A good final answer shows two NEXT: lines (the first names Sam Example) and ends with the line "Escalation: Sam Example". Fail the answer if it has more or fewer than two next steps, if a step does not start with NEXT:, if the first does not name Sam Example, or if the Escalation line is missing.
