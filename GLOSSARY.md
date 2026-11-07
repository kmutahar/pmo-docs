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
A project's own copy of a template that replaces the skill's default as a whole.
_Avoid_: customisation, patch, fork

**Playbook override**:
A project's copy of a playbook in `pmo/playbooks/` that replaces the skill's default.
_Avoid_: custom playbook, local playbook

**Drift**:
The state of a template or playbook override when the skill's default has moved to a newer version.
_Avoid_: divergence, desync

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

**Goal**:
An optional entry of the `priorities` register: an output with acceptance criteria. Tasks are not linked to goals. Not the same as a task's priority, which is a level (high, medium, low) from the vocabulary.
_Avoid_: priority (for a goal)

**Entry**:
One item in a register, with its own id (for example T-014).
_Avoid_: row, record, item, line

**Origin**:
An optional field on every entry that says where it came from: `stated` (the user said it) or `proposed` (the agent inferred it and the user has not confirmed it).
_Avoid_: source, provenance

**Vocabulary**:
The allowed values for an entry's fields, such as statuses, priority levels and severities.
_Avoid_: enum, allowed values, lookup

**Validation**:
A rule every entry must meet, set by the vocabulary and the register's fields.
_Avoid_: check, lint

**View**:
A read-only summary rendered from registers, never edited by hand.
_Avoid_: report, dashboard

**Catalogue**:
The generated view (`pmo/views/catalogue.md`) listing every doc type, when to make it, and its publish settings.
_Avoid_: document index, doc list

**Week start**:
The day a project's working week begins (`project.week_start`, default Monday).
_Avoid_: start of week, calendar start

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

**Open questions**:
The section of a document (`## Open questions`) that lists every value that is missing or unconfirmed, such as `not set` or `not provided`.
_Avoid_: TODOs, gaps, unknowns

**RAG**:
Red, amber or green: a status rating in a report. The document states the rule used.
_Avoid_: traffic light, health

**Period**:
The span of time a document covers, such as a week or a month.
_Avoid_: cycle, sprint, interval

**Document**:
One doc type written for one period (or once, where the doc type has no periods). It is a draft until it is finished.
_Avoid_: doc, output, deliverable

**Draft**:
A document that is not finished yet.
_Avoid_: working copy, WIP

**Generator**:
A script (`generate.py`) that pre-fills a document's register-derived sections before agent editing.
_Avoid_: auto-generator, builder, scaffolder

**Finish**:
The step that marks a draft finished: version recorded, comments removed, checks passed.
_Avoid_: finalise, finalize, close, complete

**Command**:
A slash command the user types to start a fixed task, `/pmo-docs:init` or `/pmo-docs:publish`. The agent never runs one on its own.
_Avoid_: recipe, skill, macro

**Publish**:
The process of copying finished documents to the configured folder or repository via `/pmo-docs:publish`.
_Avoid_: deploy, push, export, sync

**Publish target**:
Where `/pmo-docs:publish` copies finished documents, set by `publish.mode` in the config: `folder` (a folder inside the project) or `repo` (the top level of another git repository, where a commit is made only after the user says yes).
_Avoid_: destination, remote, export folder

**Publish conflict**:
The state `publish.py` reports when a file already exists at the publish target with different content. It is overwritten only with the user's yes for that file.
_Avoid_: collision, diff

**Published copy**:
The copy of a finished document written to the publish target.
_Avoid_: export, artifact, published file

**Stale**:
Said of a finished document when a register it was made from has changed since it was finished.
_Avoid_: outdated, out of date

## Languages

**Language**:
A language documents are written in (the draft language, `languages.draft`) or translated into (a translation language).
_Avoid_: locale

**Original**:
The document a translation is made from.
_Avoid_: master, source document

**Translation**:
A document in another language, next to its original as `<name>.<lang>.md`, with the same headings, tables, ids and numbers.
_Avoid_: localisation, version

## Agent work

**Made by**:
The catalogue column that says whether a document type is filled by a script (`generator`) or by the agent (`agent`).
_Avoid_: author, source

**Playbook**:
Step-by-step instructions the agent follows for one kind of request. The skill keeps them in `references/` only because the Agent Skills spec names that folder.
_Avoid_: reference, guide, procedure, mode

**Recipe**:
A named request with fixed inputs (such as weekly-status) that has its own playbook and produces a draft. It may edit registers, but never publishes or sends.
_Avoid_: workflow, command, routine, macro
