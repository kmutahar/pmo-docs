---
title: "Overdue report - {{project}}"
type: overdue-report
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: tasks, milestones, actions, risks, issues -->

# Overdue - as of {{date}}

Overdue tasks: {{overdue_tasks}}, open actions past due: {{overdue_actions}}, milestones due within {{days}} days or overdue: {{milestones_due}}, open issues: {{open_issues}}, open risks: {{open_risks}}

## Overdue tasks
<!-- overdue = due before the as-of date and not closed -->
| ID | Task | Owner | Due | Days late | Priority |
|---|---|---|---|---|---|
| {{id}} | {{title}} | {{lead}} | {{due}} | {{days_late}} | {{priority}} |

## Open actions past due
| ID | Action | Owner | Due |
|---|---|---|---|
| {{id}} | {{text}} | {{lead}} | {{due}} |

## Milestones due within {{days}} days or overdue
<!-- {{days}} is the window used (the --days option of overdue.py, default 14) -->
| ID | Milestone | Due | Status |
|---|---|---|---|
| {{id}} | {{title}} | {{due}} | {{status}} |

## Open issues by severity
<!-- most severe first -->
| ID | Issue | Severity | Owner | Status |
|---|---|---|---|---|
| {{id}} | {{title}} | {{severity}} | {{lead}} | {{status}} |

## Open risks
| ID | Risk | Probability | Impact | Owner | Status |
|---|---|---|---|---|---|
| {{id}} | {{title}} | {{probability}} | {{impact}} | {{lead}} | {{status}} |

## Bad due dates
<!-- the tool prints this section only when a due date cannot be read; otherwise keep the header and add one row: None -->
| Register | ID | Due |
|---|---|---|
| {{register}} | {{id}} | {{due}} |

## Suggested next steps
<!-- at most 5, each naming an id, a person and what to ask them; for a risk, the next step is its mitigation -->
- 

## Open questions
- 
