---
type: llm
weight: 2
---

The Acme tasks register holds T-1 to T-4, so the next task id is T-5. The final answer quotes the new task's id and the line it added. Pass only if the id is `T-5`, the quoted line holds the values the user gave (title "Write the release notes", team web, group docs, priority low, owner bob, not-started, due 2026-03-28, period 2026-03) and nothing else made up (an empty `notes` and `origin: stated` are allowed, they are not invented), and the answer does not say that any existing task was renumbered, deleted or reused. Fail the answer if the new id is anything but T-5.
