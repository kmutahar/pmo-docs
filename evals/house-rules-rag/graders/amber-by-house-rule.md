---
type: llm
weight: 3
---

The project's house rule replaces the RAG rule: red only when a milestone is overdue; amber when any task is blocked or overdue and no milestone is overdue. As of 2026-03-15 task T-001 is overdue and T-004 is blocked, and milestone M-001 is due 2026-03-20, so it is not overdue. A good final answer quotes an Overall line that is amber (naming the overdue or blocked task) and a Notes on data line that states the house rule, not the default rule. Fail the answer if Overall is red or green, or if the rule line states the default rule (a top-priority task that is overdue makes red).
