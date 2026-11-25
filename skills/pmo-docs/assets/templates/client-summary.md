---
title: "Client summary - {{project}}"
type: client-summary
project: "{{project}}"
manager: "{{manager}}"
period: "{{period}}"
template_version: 1
status: draft
last_updated: "{{date}}"
---

<!-- Reads: milestones, tasks, decisions, changes, risks -->

# Client summary - {{project}}

**Period:** {{period}}

## Where we are
<!-- Two or three plain sentences for a client who does not read registers: what is delivered, what is under way, whether the dates hold. No ids, no internal team names. -->
{{where we are}}

## Delivered
<!-- Outcomes the client can see or use, at most five bullets. -->
- {{delivered outcome}}

## Coming next
<!-- What the client will see next and when, at most five bullets. -->
- {{next outcome}} - {{date or period}}

## What we need from you
<!-- Decisions, approvals, access or content the team is waiting for. Include every proposed decision and proposed change in the decisions and changes registers. Write "- None" when nothing is waiting. -->
- {{request}}

## Changes agreed
<!-- Scope, date or cost changes accepted in the period. Write "- None" when there are none. -->
- {{change}}

## Open questions
<!-- Points to confirm with the client, and any open high-impact risk that could move a date, in plain words (for example "The payment vendor may reply late, which could delay the vendor choice"). No ids. Do not invent questions the registers do not support. State an issue or risk only as the register records it: no cause, no fix under way, no forecast. -->
- {{question}}
