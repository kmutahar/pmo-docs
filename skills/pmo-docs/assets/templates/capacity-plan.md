---
title: "Capacity plan - {{project}}"
type: capacity-plan
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: capacity, tasks, roster -->

# Capacity plan - {{project}}

**Period:** {{period}}

## Capacity by person
<!-- One row per person with capacity or open tasks, plus "unassigned". Available days = working days minus leave. Flag is green, amber or red. If working days are missing, write "not provided". -->
| Person | Working days | Leave | Available days | Open tasks | Tasks per available day | Flag |
|---|---|---|---|---|---|---|
| {{lead}} | {{working_days}} | {{leave_days}} | {{available_days}} | {{open_tasks}} | {{tasks_per_day}} | {{flag}} |

## Overloaded or at risk
<!-- First bullet states the rule used for the flag. -->
- 

## Recommendations
<!-- Name the task ids and people each move touches. -->
- 

## Open questions
- 
