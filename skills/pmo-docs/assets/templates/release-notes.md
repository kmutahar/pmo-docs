---
title: "Release notes - {{project}}"
type: release-notes
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
covers_from: "{{covers_from}}"
covers_to: "{{covers_to}}"
---

<!-- Reads: tasks, changes -->

# Release notes - {{project}}

**Period:** {{period}}

**Covers:** {{covers_from}}..{{covers_to}}

## New
<!-- Line format: - change description (`sha7`) - task-id if the commit message names one -->
- {{change}} (`{{sha7}}`)

## Improved
<!-- Line format: - change description (`sha7`) - task-id if the commit message names one -->
- {{change}} (`{{sha7}}`)

## Fixed
<!-- Line format: - change description (`sha7`) - task-id if the commit message names one -->
- {{change}} (`{{sha7}}`)

## Breaking changes
<!-- Line format: - change description (`sha7`) - task-id if the commit message names one -->
- {{change}} (`{{sha7}}`)

## Internal
<!-- Line format: - change description (`sha7`) - task-id if the commit message names one -->
- {{change}} (`{{sha7}}`)

## Docs to update
<!-- List existing documentation files needing updates, marked proposed. -->
- {{document}} ({{reason}})

## Open questions
<!-- Items to clarify, including proposed task links inferred from keywords. -->
- {{question}}
