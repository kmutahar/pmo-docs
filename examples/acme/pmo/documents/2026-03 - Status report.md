---
title: "Status report - Acme Portal"
type: status-report
project: "Acme Portal"
manager: "Sam Example"
period: "2026-03"
template_version: 1
status: draft
last_updated: "2026-03-15"
---

# Status report - Acme Portal

**Period:** 2026-03

**Overall:** red - top-priority task T-1 is overdue
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
- Write API outline `T-3`

## Planned next
- Set up staging server `T-1` - Alice Example - 2026-03-10
- Design login page `T-2` - Bob Example - 2026-03-25
- Pick a payment vendor `T-4` - Bob Example - 2026-04-01

## Blockers and decisions needed
| ID | Item | Needed from | By when |
|---|---|---|---|
| T-4 | Pick a payment vendor, waiting for budget | Bob Example | 2026-04-01 |
| DEC-2 | Host on shared cloud | Sam Example | not set |
| CR-1 | Add dark mode | not set | not set |

## Decisions and changes
| ID | Title | Status | Date |
|---|---|---|---|
| CR-1 | Add dark mode | proposed | 2026-03-06 |
| DEC-2 | Host on shared cloud | proposed | 2026-03-09 |

## Risks and issues
- Vendor delay is open `R-1`
- Login fails on staging is open `I-3`

## Milestones
| ID | Milestone | Due | Status |
|---|---|---|---|
| M-1 | Staging ready | 2026-03-20 | in-progress |

## Notes on data
- RAG rule: weekly-status, as computed by pmo_common.rag, as of 2026-03-15: red because the top-priority task T-1 is overdue.

## Open questions
- Who approves the budget for the vendor?
