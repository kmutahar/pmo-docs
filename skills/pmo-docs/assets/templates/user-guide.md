---
title: "User guide - {{project}}"
type: user-guide
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
code_ref: "{{commit}}"
checks:
  - kind: required_cells
    section: Roles and what each can do
    columns: [Can]
  - kind: required_cells
    section: Troubleshooting
    columns: [What to do]
---

<!-- Reads: requirements, permissions -->

# User guide - {{project}}

## Who this guide is for
<!-- Target audience and user personas, referencing the user-facing roles in domain.roles. -->
{{Target audience and roles}}

## Getting started
<!-- Initial onboarding and setup steps to begin using the product; numbered steps. -->
1. {{Step 1 to get started}}
2. {{Step 2 to get started}}

## How to
<!-- Step-by-step instructions for key user tasks; one task per subsection with numbered steps; screens and UI labels are read from code; the guide carries no `path:line`, the reply lists the files you read. -->
### {{what the reader wants to do}}
1. {{Step 1}}
2. {{Step 2}}

- **What you see:** {{what the reader sees after completing the steps}}
- **Who can do this:** {{roles permitted to perform this task}}

## Roles and what each can do
<!-- User capabilities and access boundaries by role, derived from the permissions register; Can is required; write "none" for an empty field. -->
| Role | Can | Cannot |
|---|---|---|
| {{role}} | {{can}} | {{cannot}} |

## Troubleshooting
<!-- Common user issues, possible causes, and resolution steps; What to do is required; write "not recorded" for an empty field. -->
| Problem | Cause | What to do |
|---|---|---|
| {{problem}} | {{cause}} | {{what_to_do}} |

## Terms
<!-- Glossary of domain and application terms the user encounters in the product. -->
| Term | Meaning |
|---|---|
| {{term}} | {{meaning}} |

## Open questions
<!-- Ambiguous user flows, unconfirmed role permissions, or undocumented edge cases; write "- None" when nothing is open. -->
- 
