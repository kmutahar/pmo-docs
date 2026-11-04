---
title: "Project plan - {{project}}"
type: project-plan
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: tasks, milestones, priorities, teams, risks, assumptions, dependencies, changes, roster -->

# Project plan - {{project}}

## Objective
<!-- One or two sentences: the outcome this plan delivers. -->

## Team
<!-- From the roster. -->
| Role | Name |
|---|---|
| {{role}} | {{name}} |

## Priorities
<!-- One subsection per priority, in register order. -->

### {{id}} - {{title}}
- {{goal}}

**Output:** {{output}}
**Depends on:** {{depends_on}}
**Owner:** {{lead}}
**Acceptance criteria:** {{acceptance}}
**Status:** {{status}} - **Due:** {{due}}

## Team assignments
<!-- One subsection per team, in register order; each task of the period that is not dropped appears once. -->

### {{team}} - {{lead}}
**{{group}}**
- {{task title}} `{{id}}`

**Output:** {{team output}}

## Dependencies and sequencing
| Priority | Depends on | Blocks |
|---|---|---|
| {{id}} | {{depends_on}} | {{blocks}} |

## Milestones
| ID | Milestone | Due | Status |
|---|---|---|---|
| {{id}} | {{title}} | {{due}} | {{status}} |

## Risks
<!-- Open and mitigating risks. -->
| ID | Risk | Probability | Impact | Owner | Mitigation |
|---|---|---|---|---|---|
| {{id}} | {{title}} | {{probability}} | {{impact}} | {{lead}} | {{mitigation}} |

## Assumptions
- {{assumption}} `{{id}}`

## Out of scope
- {{item}}

## End-of-period target
{{target}}

## Change log
<!-- The latest approved changes that touch this plan. -->
| Date | Change | Decided by |
|---|---|---|
| {{date}} | {{title}} | {{decided_by}} |

## Open questions
- {{question}}
