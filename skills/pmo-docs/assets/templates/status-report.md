---
title: "Status report - {{project}}"
type: status-report
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: tasks, milestones, risks, issues, changes, actions, decisions, teams -->

# Status report - {{project}}

**Period:** {{period}}

**Overall:** {{RAG}} - {{one-sentence reason}}
**Progress:** {{done}}/{{total}} tasks done ({{pct}}%), {{delta}} vs last report

## Summary
{{3 sentences at most: what moved, what did not, what is next}}

## Progress by priority
<!-- one row per priority level used by the tasks (a level of vocab.priority_order, not a goal) -->
| Priority | Done / Total | In progress | Blocked | RAG | Comment |
|---|---|---|---|---|---|
| {{priority}} | {{done}} / {{total}} | {{n}} | {{n}} | {{RAG}} | {{comment}} |

## Progress by team
<!-- one row per team in the teams register -->
| Team | Done / Total | In progress | Blocked | Main changes |
|---|---|---|---|---|
| {{team}} | {{done}} / {{total}} | {{n}} | {{n}} | {{changes}} |

## Completed since last report
- {{task}} `{{id}}`

## Planned next
- {{task}} `{{id}}` - {{lead}} - {{due}}

## Blockers and decisions needed
<!-- every blocked task that is not closed, whatever its period, then the open items that need a decision: who is needed and by when -->
| ID | Item | Needed from | By when |
|---|---|---|---|
| {{id}} | {{item}} | {{lead}} | {{date}} |

## Decisions and changes
<!-- entries dated in the period -->
| ID | Title | Status | Date |
|---|---|---|---|
| {{id}} | {{title}} | {{status}} | {{date}} |

## Risks and issues
- {{new, changed or closed risk or issue}} `{{id}}`

## Milestones
| ID | Milestone | Due | Status |
|---|---|---|---|
| {{id}} | {{title}} | {{due}} | {{status}} |

## Notes on data
<!-- the RAG rule used, anything inferred, unverified or missing -->

## Open questions
- {{question}}
