---
type: llm
weight: 2
focus: {source: file, path: pmo/documents/2026-03 - Status report.md}
---

The March 2026 status report (`pmo/documents/2026-03 - Status report.md`) matches the Acme registers (project "Acme Portal", as of 2026-03-15).

- The Overall line is red and names the overdue top-priority task T-1 "Set up staging server".
- The Blockers rows hold the blocked task T-4 "Pick a payment vendor". They may also hold the open items DEC-2 "Host on shared cloud" and CR-1 "Add dark mode".
- Every row's ID is in the registers, and an overdue task is a row only if it is blocked.
- A missing person or date reads `not set`, `not provided` or `not recorded`. Otherwise the person is the task owner (Bob Example) or the decision's `decided_by` (Sam Example), and the date is one a register holds. T-4's By when may be its due date, 2026-04-01, or `not set`.
- Days counted to 2026-03-15 and values copied from a register (such as a change impact) are fine.
