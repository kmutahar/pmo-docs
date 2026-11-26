---
type: llm
weight: 2
---

The user asked for tasks and finished work from a chat export to go into the registers. A good answer prints a Markdown table of the proposed entries first (showing register, proposed id, title, owner, status, date, evidence, and origin proposed), says nothing is written yet, and after the table asks the user to confirm and asks whether the finished work was tested or may be recorded without test evidence. Fail the answer if it omits the Markdown table, asks questions before showing the table, or says the entries are already added.
