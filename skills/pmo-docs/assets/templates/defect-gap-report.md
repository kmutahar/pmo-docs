---
title: "Defect and gap report - {{project}}"
type: defect-gap-report
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
checks:
  - kind: required_cells
    section: Open issues
    columns: [Severity, Lead, Status]
  - kind: required_cells
    section: Gaps
    columns: [Gap]
---

<!-- Reads: tests, issues, requirements -->

# Defect and gap report - {{project}}

**Period:** {{period}}

## Summary
<!-- Summary of defects and gaps for the period: counts must equal the entries in Defects, Open issues, and Gaps below; at most three sentences. -->
**Failed tests:** {{failed_count}} - **Open issues:** {{open_issues_count}} - **Requirements without a passing test:** {{gap_count}}

{{At most three sentences summarizing quality state, critical defects, and release readiness.}}

## Defects
<!-- One row per test in the tests register with status failed; Issue and Severity from the linked issue, or "not set" when unlinked (add to Open questions); write "not recorded" for an empty field. -->
| ID | Failed test | Requirement | Issue | Severity | Lead |
|---|---|---|---|---|---|
| {{id}} | {{test}} | {{requirement}} | {{issue}} | {{severity}} | {{lead}} |

## Open issues
<!-- From the issues register: issues whose status is not closed, ordered most severe first; Severity, Lead, and Status are required; write "not recorded" for an empty field. -->
| ID | Issue | Severity | Lead | Status | Raised |
|---|---|---|---|---|---|
| {{id}} | {{issue}} | {{severity}} | {{lead}} | {{status}} | {{raised}} |

## Gaps
<!-- Requirements whose status is not closed with no linked test, or whose tests are all failed, blocked or planned; Gap is "no test", "test failed" or "test not run" and is required. Optional second paragraph for gaps against code when folders are named. -->
| Requirement | Title | Priority | Gap |
|---|---|---|---|
| {{requirement}} | {{title}} | {{priority}} | {{gap}} |

## Recommendations
<!-- Actionable proposals addressing identified defects and gaps; each recommendation names a specific ID; proposals only, never decisions. -->
- {{recommendation naming an ID}}

## Open questions
<!-- Gaps, unlinked failed tests, missing issue details, or unresolved defects needing decision; write "- None" when nothing is open. -->
- 
