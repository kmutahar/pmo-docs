---
title: "Integration guide - {{project}}"
type: integration-guide
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
code_ref: "{{commit}}"
checks:
  - kind: listed_have_sections
    listed_in: Consumers at a glance
    sections_in: Consumers
    level: 3
  - kind: required_cells
    section: Consumers at a glance
    columns: [Calls, Auth]
---

<!-- Reads: environments, permissions -->
<!-- The consumers are the names in technical.consumers, in that order; if none configured, ask for the names and offer to write them to config only after a yes. -->

# Integration guide - {{project}}

## Purpose and audience
<!-- What this integration guide covers, which external systems integrate with the API, and target audience. -->
{{Purpose and audience of the integration guide}}

## Before you start
<!-- Prerequisites for integration: access to request, required tools, and configuration variable names (never values). -->
- {{access to request}}
- {{tools required}}
- {{configuration variable name}}

## Authentication
<!-- Step-by-step procedure to authenticate requests to the API. -->
1. {{Step 1 to authenticate}}
2. {{Step 2 to authenticate}}

## Consumers at a glance
<!-- Summary of consumers from technical.consumers in order; Calls and Auth are required; write "not recorded" for an empty field. -->
| Consumer | Calls | Auth |
|---|---|---|
| {{consumer}} | {{calls}} | {{auth}} |

## Consumers
<!-- One subsection per consumer matching the order in Consumers at a glance; detail endpoints, roles, and handling; write "not recorded" for an empty field. -->
### {{consumer}}
- **What it calls:** {{what it calls}}
- **Endpoints used:** {{endpoints used}}
- **Roles it needs:** {{roles it needs}}
- **Differences by environment:** {{differences by environment}}
- **Failure handling:** {{failure handling}}

## Environments
<!-- Environments from the environments register; Base address from location without URLs; write "not recorded" for an empty field. -->
| Environment | Base address | Differences |
|---|---|---|
| {{environment}} | {{base_address}} | {{differences}} |

## Errors and retries
<!-- Common failure situations and recommended consumer handling or retry behavior; write "not recorded" for an empty field. -->
| Situation | What the consumer does |
|---|---|
| {{situation}} | {{what_the_consumer_does}} |

## Go-live checklist
<!-- Verification steps before enabling live traffic for a consumer. -->
- [ ] {{Pre-integration verification step}}
- [ ] {{Access and credentials confirmed}}
- [ ] {{Health check and smoke test passed}}

## Open questions
<!-- Missing consumer requirements, unresolved environment differences, or unconfirmed access details; write "- None" when nothing is open. -->
- 
