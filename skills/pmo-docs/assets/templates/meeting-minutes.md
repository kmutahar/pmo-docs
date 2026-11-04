---
title: "Meeting minutes {{date}}"
type: meeting-minutes
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: meetings, actions, decisions -->

# Meeting minutes - {{title}} - {{date}}

<!-- Absent and Purpose are not meetings fields: fill them by hand, or write "not recorded". -->
**Meeting:** {{id}}
**Attendees:** {{attendees}}
**Absent:** {{absent}}
**Purpose:** {{purpose}}

## Decisions
<!-- Facts only; every decision and action carries its register ID. -->
| ID | Decision | Decided by |
|---|---|---|
| {{id}} | {{decision}} | {{decided_by}} |

## Actions
| ID | Action | Owner | Due |
|---|---|---|---|
| {{id}} | {{text}} | {{lead}} | {{due}} |

## Discussion summary
<!-- One bullet per topic, outcome first. -->
- {{topic}}

## Next meeting
{{date and topic, or "not set"}}

## Open questions
- {{question}}
