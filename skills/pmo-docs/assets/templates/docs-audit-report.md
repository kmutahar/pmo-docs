---
title: "Documentation audit - {{project}}"
type: docs-audit-report
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 2
status: draft
last_updated: "{{date}}"
---

<!-- Reads: -->

# Documentation audit - {{project}}

**Period:** {{period}}

**Scope:** {{all documents or a folder}} - **Files scanned:** {{n}} - **Findings:** {{total}}

## Summary
<!-- one row per check, with the count (0 is a valid count); checks not run go under Not checked -->
| Check | Findings |
|---|---|
| Register validity | |
| Front matter | |
| Stale | |
| Old | |
| Broken links | |
| Override drift | |
| Structure vs template | |
| Document vs register | |
| Drift vs code | |

## Findings
<!-- severity: high = wrong, medium = stale, low = naming or front matter; evidence is a file and line or the command that showed it -->
| # | Severity | Check | Document | Problem | Evidence | Suggested fix |
|---|---|---|---|---|---|---|
| {{n}} | {{severity}} | {{check}} | {{document}} | {{problem}} | {{evidence}} | {{fix}} |

## Drift vs code
<!-- what a document claims against what the code does, with a file and line on both sides -->
| Document | Claim | Code reality | Evidence |
|---|---|---|---|
| {{document}} | {{claim}} | {{reality}} | {{evidence}} |

## Fixes applied
<!-- only when the run was allowed to fix; otherwise write "None (no fixes requested)" -->
- 

## Not checked
- 

## Open questions
- 
