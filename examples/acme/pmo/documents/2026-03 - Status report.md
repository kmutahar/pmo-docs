---
title: "Status report - Acme Portal"
type: status-report
project: "Acme Portal"
manager: "Sam Example"
period: "2026-03"
template_version: 2
status: draft
last_updated: "2026-03-15"
---

# Status report - Acme Portal

**Period:** 2026-03

**Overall:** red - top-priority task T-001 is overdue
**Progress:** 1/4 tasks done (25%), first report so no comparison

## Summary
Staging is late and the vendor choice is blocked. The API outline is done. Next is the login page design.

## Progress by priority
| Priority | Done / Total | In progress | Blocked | RAG | Comment |
|---|---|---|---|---|---|
| high | 0 / 1 | 1 | 0 | red | Staging is overdue |
| medium | 0 / 2 | 0 | 1 | amber | Vendor choice waits for budget |
| low | 1 / 1 | 0 | 0 | green | API outline done |

## Progress by team
| Team | Done / Total | In progress | Blocked | Main changes |
|---|---|---|---|---|
| Platform | 1 / 2 | 1 | 0 | API outline done, staging in progress |
| Web | 0 / 2 | 0 | 1 | Login design not started |

## Completed since last report
- Write API outline `T-003`

## Planned next
- Set up staging server `T-001` - Alice Example - 2026-03-10
- Design login page `T-002` - Bob Example - 2026-03-25
- Pick a payment vendor `T-004` - Bob Example - 2026-04-01

## Blockers and decisions needed
| ID | Item | Needed from | By when |
|---|---|---|---|
| T-004 | Pick a payment vendor, waiting for budget | Bob Example | 2026-04-01 |
| DEC-002 | Host on shared cloud | Sam Example | not set |
| CR-001 | Add dark mode | not set | not set |

## Decisions and changes
| ID | Title | Status | Date |
|---|---|---|---|
| CR-001 | Add dark mode | proposed | 2026-03-06 |
| DEC-002 | Host on shared cloud | proposed | 2026-03-09 |

## Risks and issues: changes since last report
- Vendor delay is open `R-001`
- Login fails on staging is open `I-003`

## Milestones
| ID | Milestone | Due | Status |
|---|---|---|---|
| M-001 | Staging ready | 2026-03-20 | in-progress |

## Notes on data
- RAG rule: weekly-status; overdue measured at 2026-03-15; registers read on 2026-03-15: red because the top-priority task T-001 is overdue.

## Open questions
- Who approves the budget for the vendor?
