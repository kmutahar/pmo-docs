---
title: "API reference - {{project}}"
type: api-reference
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
code_ref: "{{commit}}"
checks:
  - kind: required_cells
    section: Authentication and permissions
    columns: [Allowed roles]
  - kind: required_cells
    section: Environments
    columns: [Base address]
---

<!-- Reads: environments, permissions -->

# API reference - {{project}}

## Overview
<!-- What the API is for, versioning, and the authentication scheme in one line each. -->
{{What the API is for}}
{{API versioning scheme}}
{{Authentication scheme in one line}}

## Authentication and permissions
<!-- Resource access rules and required roles from the permissions register; Allowed roles is required; write "not recorded" for an empty field. -->
| Resource | Action | Allowed roles | Condition |
|---|---|---|---|
| {{resource}} | {{action}} | {{allowed_roles}} | {{condition}} |

## Endpoints
<!-- Endpoints extracted from code: path, method, roles, parameters/body, response, errors, and code location with path:line; write "not recorded" for an empty field. -->
### {{METHOD}} {{path}}
- **Purpose:** {{purpose}}
- **Access:** {{roles}}
- **Request:** {{parameters and body fields}}
- **Response:** {{response structure or status}}
- **Errors:** {{status codes and reasons}}
- **Code:** {{path:line}}

## Errors
<!-- Standard error responses, HTTP status codes, meaning, and when they occur; write "not recorded" for an empty field. -->
| Status | Meaning | When it happens |
|---|---|---|
| {{status}} | {{meaning}} | {{when_it_happens}} |

## Environments
<!-- Deployment environments from the environments register; Base address is the environment's `location`, never a link that holds a password, and is required; write "not recorded" for an empty field. -->
| Environment | Base address | Notes |
|---|---|---|
| {{environment}} | {{base_address}} | {{notes}} |

## Open questions
<!-- Undocumented endpoints, missing permission rules, or unconfirmed parameters; write "- None" when nothing is open. -->
- {{question}}
