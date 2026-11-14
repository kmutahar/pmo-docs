---
title: "Entity lifecycle - {{entity}}"
type: entity-lifecycle
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
code_ref: "{{commit}}"
checks:
  - kind: required_cells
    section: Transitions
    columns: [From, To, Trigger]
  - kind: required_cells
    section: Who can do what
    columns: [Allowed roles]
---

<!-- Reads: permissions -->
<!-- {{entity}} is domain.lifecycle_entity; when null, ask which entity. Roles are written as the code names them and compared with domain.roles; any role not in domain.roles goes to Open questions. -->

# Entity lifecycle - {{entity}}

## Entity
<!-- What the entity is, what domain concept it represents, and where it is defined in code with path:line. -->
{{Description of the entity and its role in the system}}

**Defined in:** {{path:line}}

## States
<!-- Lifecycle states of the entity, their meaning, entry condition, and whether final; write "not recorded" for an empty field. -->
| State | Meaning | Entered when | Final |
|---|---|---|---|
| {{state}} | {{meaning}} | {{entered_when}} | {{final}} |

## Transitions
<!-- Valid state transitions, their trigger (action or event), and code location with path:line; From, To, and Trigger are required. -->
| From | To | Trigger | Code |
|---|---|---|---|
| {{from}} | {{to}} | {{trigger}} | {{path:line}} |

## Who can do what
<!-- Actions on the entity and allowed roles; from permissions register and code findings (marked as proposals); Allowed roles is required. -->
| Action | Allowed roles | Condition | Source |
|---|---|---|---|
| {{action}} | {{allowed_roles}} | {{condition}} | {{source}} |

## Rules and side effects
<!-- Business rules, validations, side effects (notifications, events, audit rows) triggered by entity changes; write "None" if none. -->
- {{validation, notification or audit rule with path:line}}

## Gaps
<!-- Inconsistencies found in code or registers: non-final state without outgoing transition, transition no role can perform, permission without transition; write "None" if clean. -->
- {{gap or inconsistency identified}}

## Open questions
<!-- Disputed transitions, unlisted roles, or ambiguous lifecycle rules; write "- None" when nothing is open. -->
- 
