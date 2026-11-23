---
type: llm
weight: 2
focus: {source: file, path: pmo/documents/Work order.md}
---

The work order draft (`pmo/documents/Work order.md`) is a draft for "Acme Portal" (as of 2026-03-15) that matches the Acme registers:

- Front matter has `type: work-order` and `status: draft`, and the title names the work, "Staging and login".
- The Tasks table lists the open tasks `T-001` "Set up staging server", `T-002` "Design login page" and `T-004` "Pick a payment vendor" with their owners (Alice Example for `T-001`, Bob Example for `T-002` and `T-004`) and due dates from the register. `T-003` is done and is not listed.
- Assigned to names the roster people Alice Example and Bob Example (not raw slugs); Issued is 2026-03-15.
- Milestones, requirements and budget entries may appear (for example as constraints or acceptance), but none is required, and none is invented.
- A missing person or date reads `not set`, `not provided` or `not recorded`; otherwise the person comes from a register or the roster and the date from a register.
