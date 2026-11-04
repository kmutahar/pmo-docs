# pmo-docs

A project office kept in plain files: an agent tracks a project's facts and drafts its documents from them. One word per concept; the words under _Avoid_ mean the same thing and are not used.

## Where things live

**Skill**:
The shared engine: rules, playbooks, default templates and scripts, the same for every project.
_Avoid_: engine, plugin (the plugin is only a way of installing the skill)

**Project**:
A user's repository that uses the skill and keeps its own settings, registers and documents.
_Avoid_: workspace, instance, client

**Override**:
A project's own copy of a template or playbook that replaces the skill's default as a whole.
_Avoid_: customisation, patch, fork

**House rules**:
The project's own rules, added to the skill's rules.
_Avoid_: project rules, conventions, local rules

## People

**Project manager**:
The person who runs the project and is named on its documents.
_Avoid_: owner, lead, sponsor

**Owner**:
The person responsible for one entry, named by their roster slug.
_Avoid_: assignee, responsible

**Roster**:
The register of the project's people: one entry per person with a slug, name and role.
_Avoid_: members, people list, team (a team is a work stream)

## Facts

**Register**:
A file holding every entry of one kind (tasks, risks, issues, decisions, ...). Registers are the only source of facts.
_Avoid_: tracker, log, list, database

**Entry**:
One item in a register, with its own id (for example T-014).
_Avoid_: row, record, item, line

**Vocabulary**:
The allowed values for an entry's fields, such as statuses, priorities and severities.
_Avoid_: enum, allowed values, lookup

**Validation**:
A rule every entry must meet, set by the vocabulary and the register's fields.
_Avoid_: check, lint

**View**:
A read-only summary rendered from registers, never edited by hand.
_Avoid_: report, dashboard

## Documents

**Doc type**:
A kind of document the project produces, such as a project charter or a weekly status report.
_Avoid_: document kind, template type

**Template**:
The skeleton and contract of one doc type: the sections a document must have and the checks it must pass. The checks are declared in the template's own front matter, so an override carries its own.
_Avoid_: form, skeleton, boilerplate

**Check**:
A rule a draft must meet, declared in the front matter of its doc type's template. A check that names a missing section fails.
_Avoid_: lint, test

**Period**:
The span of time a document covers, such as a week or a month.
_Avoid_: cycle, sprint, interval

**Document**:
One doc type written for one period (or once, where the doc type has no periods). It is a draft until it is finished.
_Avoid_: doc, output, deliverable

**Draft**:
A document that is not finished yet.
_Avoid_: working copy, WIP

**Finish**:
The step that marks a draft finished: version recorded, comments removed, checks passed.
_Avoid_: finalise, finalize, close, complete

**Stale**:
Said of a finished document when a register it was made from has changed since it was finished.
_Avoid_: outdated, out of date

## Agent work

**Playbook**:
Step-by-step instructions the agent follows for one kind of request. The skill keeps them in `references/` only because the Agent Skills spec names that folder.
_Avoid_: reference, guide, procedure, mode

**Recipe**:
A named request with fixed inputs (such as weekly-status) that has its own playbook and produces a draft. It may edit registers, but never publishes or sends.
_Avoid_: workflow, command, routine, macro
