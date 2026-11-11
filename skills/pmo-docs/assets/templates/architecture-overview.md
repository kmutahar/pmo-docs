---
title: "Architecture overview - {{project}}"
type: architecture-overview
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
code_ref: "{{commit}}"
checks:
  - kind: required_cells
    section: Components
    columns: [Responsibility, Location]
  - kind: required_cells
    section: Runtime and environments
    columns: [Location]
---

<!-- Reads: environments, decisions -->

# Architecture overview - {{project}}

## Context
<!-- What the system is, who uses it, and its external context; include one diagram as a fenced text block or a list (no image). -->
{{What the system is and who uses it}}

```text
{{System context diagram or text box representation}}
```

## Components
<!-- Major functional modules or packages, their purpose, technology stack, and folder or path:line location; Responsibility and Location are required. -->
| Component | Responsibility | Technology | Location |
|---|---|---|---|
| {{component}} | {{responsibility}} | {{technology}} | {{location}} |

## Data and models
<!-- Primary domain entities, their role, and definition location in code (path:line); write "not recorded" for an empty field. -->
| Entity | Purpose | Defined in |
|---|---|---|
| {{entity}} | {{purpose}} | {{defined_in}} |

## Runtime and environments
<!-- Runtime deployment targets from the environments register; Location is required; write "not recorded" for an empty field. -->
| Environment | Kind | Location | Deploy |
|---|---|---|---|
| {{environment}} | {{kind}} | {{location}} | {{deploy}} |

## Cross-cutting concerns
<!-- System-wide patterns and mechanisms with code references (path:line); one line each for authentication, configuration, logging, and error handling. -->
- **Authentication:** {{authentication mechanism with path:line}}
- **Configuration:** {{configuration handling with path:line}}
- **Logging:** {{logging approach with path:line}}
- **Errors:** {{error handling strategy with path:line}}

## Key decisions
<!-- Architectural decisions from the decisions register; ID in backticks (`DEC-1`); write "not recorded" for an empty field. -->
| ID | Decision | Status |
|---|---|---|
| `{{id}}` | {{decision}} | {{status}} |

## Open questions
<!-- Architectural uncertainties, unconfirmed dependencies, or pending technical decisions; write "- None" when nothing is open. -->
- 
