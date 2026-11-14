---
title: "Test acceptance - {{project}}"
type: test-acceptance
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
checks:
  - kind: required_cells
    section: Test cases
    columns: [Expected, Status]
  - kind: required_cells
    section: Requirements coverage
    columns: [Tests]
---

<!-- Reads: tests, requirements, environments -->

# Test acceptance - {{project}}

**Period:** {{period}}

## Scope
<!-- Summary of what is tested in this acceptance round and what is excluded; write "not recorded" if undefined. -->
{{Summary of the acceptance round scope}}

## Test environment
<!-- From the environments register: entries of kind test or staging, in id order; write "not recorded" for an empty field, never invent one. -->
| ID | Environment | Location | Branch |
|---|---|---|---|
| {{id}} | {{environment}} | {{location}} | {{branch}} |

## Test cases
<!-- From the tests register: test cases for this round, ordered by id; Expected and Status are required; write "not recorded" for an empty field, never invent one. -->
| ID | Test | Kind | Requirement | Expected | Status | Run on |
|---|---|---|---|---|---|---|
| {{id}} | {{test}} | {{kind}} | {{requirement}} | {{expected}} | {{status}} | {{run_on}} |

## Results
<!-- Summary of test outcomes: counts must equal the rows in the Test cases table; skipped tests are counted in the second sentence. -->
**Results:** {{passed}} passed, {{failed}} failed, {{blocked}} blocked, {{not_run}} not run. {{skipped}} skipped.

## Requirements coverage
<!-- From the requirements register: one row per requirement; Status is covered, failing or not covered; Tests is required. -->
| Requirement | Title | Tests | Status |
|---|---|---|---|
| {{requirement}} | {{title}} | {{tests}} | {{status}} |

## Acceptance sign-off
<!-- Left for the people who sign; Decision and Date are written "not set" until sign-off; never fill them for the signers. -->
| Role | Name | Decision | Date |
|---|---|---|---|
| {{role}} | {{lead}} | not set | not set |

## Open questions
<!-- Questions that block acceptance or need clarification; write "- None" when nothing is open. -->
- {{question}}
