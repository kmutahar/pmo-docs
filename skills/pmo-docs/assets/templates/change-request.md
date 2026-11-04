---
title: "Change request {{id}}"
type: change-request
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: changes -->

# Change request {{id}} - {{title}}

| Field | Value |
|---|---|
| Requested by | {{requested_by}} |
| Date | {{date}} |
| Status | {{status}} |
| Related tasks | {{related_tasks}} |

## Change requested
{{description}}

## Reason
<!-- Not a changes field: write it from the request, or "not recorded". -->
{{reason}}

## Impact
<!-- Fill each row with IDs and numbers from the registers, or "none". -->
| Area | Impact |
|---|---|
| Scope | {{impact}} |
| Schedule | {{impact}} |
| Owner / capacity | {{impact}} |
| Other priorities | {{impact}} |
| Risks | {{impact}} |

## Options considered
<!-- One to three options, including "do not change", each with its effect on schedule and scope. -->
1. {{option}}

## Recommendation
{{recommendation}}

## Decision
<!-- Filled only from the register once the decision is recorded. -->
| Decided by | Date | Outcome |
|---|---|---|
| {{decided_by}} | {{decided_on}} | {{status}} |

## After approval
- [ ] Registers updated
- [ ] Documents regenerated
- [ ] Decision logged
- [ ] Team informed

## Open questions
- {{question}}
