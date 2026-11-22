---
title: "Scope and work breakdown - {{project}}"
type: scope-wbs
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
checks:
  - kind: required_cells
    section: Work breakdown
    columns: [Deliverable, Owner]
---

<!-- Reads: requirements, tasks, milestones, objectives, roster -->

# Scope and work breakdown - {{project}}

## In scope
<!-- What the project delivers, one bullet per deliverable, in the client's words. -->
- {{deliverable}}

## Out of scope
<!-- What was asked about or assumed and is not included. Write "- None" when nothing was excluded. -->
- {{exclusion}}

## Work breakdown
<!-- One row per deliverable: its parts, the owner (a name from the roster), the milestone it belongs to and the ids of the tasks and requirements behind it. -->
| Deliverable | Parts | Owner | Milestone | Tasks and requirements |
|-------------|-------|-------|-----------|------------------------|
| {{deliverable}} | {{parts}} | {{lead}} | {{milestone title}} | {{ids}} |

## Assumptions
<!-- What the scope relies on, one bullet each. Write "- None" when there are none. -->
- {{assumption}}

## Open questions
<!-- Scope points still to confirm. -->
- {{question}}
