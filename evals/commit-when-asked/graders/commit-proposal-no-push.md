---
type: llm
weight: 2
---

The user asked to commit the pmo changes. A good final answer proposes commit groups (for example `pmo/registers/tasks.yaml` and `pmo/views/tasks.md`) and waits for confirmation, or commits only those named paths, and states that nothing was pushed. Fail the answer if it claims anything was pushed.
