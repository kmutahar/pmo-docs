---
title: "Roadmap - {{project}}"
type: roadmap
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
checks:
  - kind: required_cells
    section: Milestones
    columns: [Owner, Due, Exit criteria, Depends on]
---

<!-- Reads: milestones, priorities, dependencies -->

# Roadmap - {{project}}

## Now ({{period}})
<!-- One row per priority of the period. -->
| ID | Item | Owner | Target | Status |
|---|---|---|---|---|
| {{id}} | {{title}} | {{lead}} | {{due}} | {{status}} |

## Next
<!-- Target month is YYYY-MM. Items given by the user; move columns only by a change request. -->
| Item | Why next | Depends on | Target month |
|---|---|---|---|
| {{item}} | {{reason}} | {{id}} | {{target_month}} |

## Later
| Item | Notes | Target month |
|---|---|---|
| {{item}} | {{notes}} | {{target_month}} |

## Milestones
<!-- One row per milestone; write "not set" where the register has no value and add an open question. -->
| ID | Milestone | Owner | Due | Exit criteria | Depends on | Status |
|---|---|---|---|---|---|---|
| {{id}} | {{title}} | {{lead}} | {{due}} | {{exit_criteria}} | {{depends_on}} | {{status}} |

## Open questions
- 
