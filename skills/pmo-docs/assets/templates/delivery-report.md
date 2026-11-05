---
title: "Delivery report - {{project}}"
type: delivery-report
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: tasks, milestones, priorities, issues, risks, changes -->

# Delivery report - {{project}}

**Period:** {{period}}

## Summary
<!-- Numbers come from the tasks of the period: delivered + dropped + carried over = planned. -->
**Planned:** {{total}} tasks - **Delivered:** {{done}} ({{pct}}%) - **Dropped:** {{dropped}} - **Carried over:** {{carry}}

## Deliverables
<!-- One row per goal (an entry of the priorities register); delivered is yes, partly or no; acceptance met is yes, no or not verified; evidence is concrete or "none yet". -->
| Goal | Output | Owner | Delivered | Acceptance met | Evidence |
|---|---|---|---|---|---|
| {{id}} | {{output}} | {{lead}} | {{delivered}} | {{acceptance_met}} | {{evidence}} |

## Milestones
| ID | Milestone | Due | Result |
|---|---|---|---|
| {{id}} | {{title}} | {{due}} | {{result}} |

## Changes during the period
| CR | Change | Decision |
|---|---|---|
| {{id}} | {{title}} | {{status}} |

## Not delivered and why
| Item | Reason | New plan |
|---|---|---|
| {{item}} | {{reason}} | {{plan}} |

## Issues and risks that occurred
- 

## Lessons learned
- 

## Carried to next period
- {{task}} `{{id}}`

## Open questions
- 
