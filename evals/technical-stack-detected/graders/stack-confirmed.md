---
type: llm
weight: 2
---

The project's `technical.stacks` is empty, and the codebase is an Express app. The final reply passes when all three hold:
- It names Express as the stack found in the code.
- It asks the user to confirm Express (a yes/no or "name another" question).
- It says nothing has been written, or that the draft waits for the user's answer. A second question in the same message is allowed, and the draft waiting for both answers counts.
The reply fails if it says it wrote `pmo/documents/API reference.md`, or if it never asks about the stack.
