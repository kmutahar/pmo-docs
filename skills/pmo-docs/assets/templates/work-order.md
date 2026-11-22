---
title: "Work order - {{title}}"
type: work-order
project: "{{project}}"
manager: "{{manager}}"
template_version: 1
status: draft
last_updated: "{{date}}"
checks:
  - kind: required_cells
    section: Tasks
    columns: [Task, Owner, Due]
---

<!-- Reads: tasks, milestones, requirements, roster, budget -->
<!-- One work order hands a defined piece of work to one team or person. {{title}} names that piece of work. -->

# Work order - {{title}}

**Assigned to:** {{lead}}
**Issued:** {{date}}
**Due:** {{due date}}

## Purpose
<!-- Why the work is needed, in two or three sentences. -->
{{purpose}}

## Scope
<!-- What the work covers and what it does not, one bullet each. -->
- {{scope item}}

## Tasks
<!-- One row per task from the tasks register that belongs to this work; the id goes in the Task cell after the title. -->
| Task | Owner | Due |
|------|-------|-----|
| {{task title}} `{{id}}` | {{lead}} | {{due date}} |

## Acceptance
<!-- How the issuer will accept the work: one checkable statement per bullet, taken from the requirements or the tasks' acceptance. -->
- {{criterion}}

## Budget and constraints
<!-- Budget line, hours or limits that apply, or "none" when the project sets none. -->
{{budget and constraints}}

## Open questions
<!-- Points to settle before work starts. -->
- {{question}}
