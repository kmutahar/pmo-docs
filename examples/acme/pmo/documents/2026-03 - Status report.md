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

**Overall:** amber - staging is late and the payment vendor is not chosen
**Progress:** 1/4 tasks done (25%), first report so no comparison

## Summary
Staging is late and the vendor choice is blocked. The API outline is done. Next is the login page design.

## Progress by priority
| Priority | Done / Total | In progress | Blocked | RAG | Comment |
|---|---|---|---|---|---|
| high | 0 / 1 | 1 | 0 | amber | Staging is overdue |
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
- Design login page `T-2` - bob - 2026-03-25
- Set up staging server `T-1` - alice - 2026-03-10

## Blockers and decisions needed
| ID | Item | Needed from | By when |
|---|---|---|---|
| T-4 | Pick a payment vendor, waiting for budget | sam | 2026-04-01 |
| T-1 | Set up staging server, overdue | alice | 2026-03-10 |

## Decisions and changes
| ID | Title | Status | Date |
|---|---|---|---|
| DEC-2 | Host on shared cloud | proposed | 2026-03-09 |
| CR-1 | Add dark mode | proposed | 2026-03-06 |

## Risks and issues
- Vendor delay is open `R-1`
- Login fails on staging is open `I-3`

## Milestones
| ID | Milestone | Due | Status |
|---|---|---|---|
| M-1 | Staging ready | 2026-03-20 | in-progress |

## Notes on data
Overall is amber because a task is overdue and another is blocked.

## Open questions
- Who approves the budget for the vendor?
