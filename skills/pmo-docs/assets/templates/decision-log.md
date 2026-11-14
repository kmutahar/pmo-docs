---
title: "Decision log - {{project}}"
type: decision-log
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
checks:
  - kind: equal_count
    rows_in: Summary
    headings_in: Decisions
    level: 3
---

<!-- Reads: decisions -->

# Decision log - {{project}}

## Summary
<!-- one row per decision, in id order; the Decision column holds the decision text, the Status column says whether it is proposed -->
| ID | Decision | Status | Date | Decided by |
|---|---|---|---|---|
| {{id}} | {{decision}} | {{status}} | {{date}} | {{decided_by}} |

## Decisions
<!-- same order as the Summary; write the empty-value word (`SKILL.md`, Empty values) for an empty field, never invent one -->
### {{id}} - {{title}}
- **Status:** {{status}} - **Date:** {{date}} - **Decided by:** {{decided_by}}
- **Context:** {{context}}
- **Decision:** {{decision}}
- **Options considered:** {{options or "not recorded"}}
- **Consequences:** {{consequences or "not recorded"}}
- **Supersedes / related:** {{ids or "none"}}

## Open questions
- {{question}}
