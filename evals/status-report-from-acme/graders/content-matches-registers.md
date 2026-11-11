---
type: llm
weight: 2
---

The final answer quotes the "Overall" line and the "Blockers and decisions needed" rows of a March 2026 status report for the Acme registers (project "Acme Portal", as of 2026-03-15). The Overall line is red and names the overdue top-priority task T-1 "Set up staging server". The Blockers rows hold the blocked task T-4 "Pick a payment vendor" and may also hold the open items that need a decision: DEC-2 "Host on shared cloud" and CR-1 "Add dark mode". A missing person or date is written as `not set`, `not provided` or `not recorded`; the task's owner (Bob Example) or the decision's `decided_by` (Sam Example) may be named as the person needed. For T-4 the By when may be its own due date, 2026-04-01 (with or without a note such as "task due date"), or `not set`; Needed from may be Bob Example, `not set` or `not recorded`. Days counted from a register date to 2026-03-15 and values copied from a register (such as a change impact) are fine. Fail the answer if a row names an ID that is not in the registers, has a row for an overdue task that is not blocked, or gives an owner or date that no register holds.
