---
title: "Functional requirements - {{project}}"
type: functional-requirements
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
checks:
  - kind: equal_count
    rows_in: Summary
    headings_in: Requirements
    level: 3
  - kind: required_cells
    section: Summary
    columns: [Priority, Status]
---

<!-- Reads: requirements -->

# Functional requirements - {{project}}

## Summary
<!-- From the requirements register: functional requirements only (kind is functional), ordered by priority (vocab.priority_order) then id; write "not recorded" for an empty field, never invent one. -->
| ID | Requirement | Priority | Status |
|---|---|---|---|
| {{id}} | {{requirement}} | {{priority}} | {{status}} |

## Requirements
<!-- One subsection per functional requirement in the same order as the Summary; write "not recorded" for an empty field, "none" for linked tasks, never invent one. -->
### {{id}} - {{title}}
- **Priority:** {{priority}} - **Status:** {{status}} - **Lead:** {{lead}}
- **Description:** {{description}}
- **Acceptance criteria:** {{acceptance or "not recorded"}}
- **Source:** {{source or "not recorded"}}
- **Linked tasks:** {{tasks or "none"}}

## Quality and constraints
<!-- From the requirements register: non-functional requirements (kind is quality or constraint), ordered by priority then id; write "not recorded" for an empty field, never invent one. -->
| ID | Requirement | Kind | Acceptance | Status |
|---|---|---|---|---|
| {{id}} | {{requirement}} | {{kind}} | {{acceptance}} | {{status}} |

## Out of scope
<!-- Features, qualities or constraints explicitly excluded from scope for this release or phase; write "None" if nothing is excluded. -->
- {{item out of scope}}

## Open questions
<!-- Questions that need decisions from stakeholders or the team; write "- None" when nothing is open. -->
- {{question}}
