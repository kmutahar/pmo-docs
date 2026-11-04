---
title: "Team checklist - {{project}}"
type: team-checklist
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: tasks, teams, milestones -->

# Team checklist - {{project}}

Tick a task only when it is finished and tested.

**Progress:** {{done}}/{{total}} done ({{pct}}%) - **Blocked:** {{blocked}}

<!-- One section per team, in register order; a box is ticked only when the task is done in the register. -->
## {{team}} - {{lead}}

**{{group}}**
- [ ] {{task title}} `{{id}}` - {{priority}} - {{due}}

**Output:** {{team output}}

## End-of-period target check
- [ ] {{milestone title}} `{{id}}`

## Open questions
- {{question}}
