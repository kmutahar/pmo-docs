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

**Stack**:
The technology or framework the project code is built on (for example Next.js, Express, Django).
_Avoid_: technology, tech stack, platform

**Stack file**:
A one-page reference file (`references/stacks/<stack>.md` or `pmo/playbooks/stacks/<stack>.md`) with standard headings explaining where routes, models, permissions, config and tests live in a stack.
_Avoid_: tech guide, cheat sheet, framework guide

**Launcher**:
The project script (`pmo/bin/pmo`) that finds the installed skill and runs one of its scripts with the project root set.
_Avoid_: wrapper, runner, CLI, entrypoint

**pmo/.me**:
A local, untracked file holding the roster slug of the current writer.
_Avoid_: user config, identity file

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

**Editor**:
The roster slug named on a draft document, identifying who is currently editing it.
_Avoid_: author, writer, assignee

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

**Renumber**:
Fixing duplicate ids after a merge with `renumber.py`: the first copy (or keeper) keeps the id, later copies get the next free numbers and move to the end of the list, and confirmed references are rewritten.
_Avoid_: re-id, reassign, relabel

**View**:
A read-only summary rendered from registers, never edited by hand.
_Avoid_: report, dashboard

**Catalogue**:
The generated view (`pmo/views/catalogue.md`) listing every doc type, when to make it, and its publish settings.
_Avoid_: document index, doc list

**Week start**:
The day a project's working week begins (`project.week_start`, default Monday).
_Avoid_: start of week, calendar start

**Requirement**:
An entry of the `requirements` register (`REQ-`): a functional or technical condition the product must meet.
_Avoid_: spec, feature request, demand

**Test**:
An entry of the `tests` register (`TST-`): a test case or verification item linked to tasks or requirements. Not the same as a check on a document.
_Avoid_: check, test spec

**Environment**:
An entry of the `environments` register (`ENV-`): a runtime context (e.g. dev, staging, prod) where the product runs.
_Avoid_: stage, tier, deployment

**Permission**:
An entry of the `permissions` register (`PERM-`): an access rule mapping a role or action to an entity or operation.
_Avoid_: right, privilege, auth rule, ACL

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

**Technical document**:
A document drafted from the code or technical registers, such as an API reference, integration guide, architecture overview, user guide or entity lifecycle.
_Avoid_: engineering doc, code doc, system doc

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
A slash command the user types to start a fixed task, `/pmo-docs:init` or `/pmo-docs:publish`. The agent never starts one on its own.
_Avoid_: recipe, skill, macro

**Publish**:
The process of copying finished documents to the configured folder or repository with `publish.py`: the user types `/pmo-docs:publish`, or the agent shows the dry-run listing and copies after the user says yes.
_Avoid_: deploy, push, export, sync

**Publish target**:
Where `/pmo-docs:publish` copies finished documents, set by `publish.mode` in the config: `folder` (a folder inside the project) or `repo` (the top level of another git repository, where a commit is made only after the user says yes).
_Avoid_: destination, remote, export folder

**Publish conflict**:
The state `publish.py` reports when a file already exists at the publish target with different content. It is overwritten only with the user's yes for that file. A finished document that fails the structure check is reported as invalid and is never copied.
_Avoid_: collision, diff

**Published copy**:
The copy of a finished document written to the publish target.
_Avoid_: export, artifact, published file

**Stale**:
Said of a finished document when a register it was made from has changed since it was finished. A draft is behind when the registers it records changed since it was made.
_Avoid_: outdated, out of date

## Languages

**Language**:
A language documents are written in (the draft language, `languages.draft`) or translated into (a translation language).
_Avoid_: locale

**Original**:
The document a translation is made from.
_Avoid_: master, source document

**Translation**:
A document in another language, next to its original as `<name>.<lang>.md`, with the same headings, tables, ids, numbers, list items and ticked boxes.
_Avoid_: localisation, version

**Parity**:
The state of a translation that has the same headings, tables, ids, numbers, list items and ticked boxes as its original (`parity_check.py`).
_Avoid_: match, sync

**Translation glossary**:
The approved and proposed term lists of one language. The agent reads the approved list and only appends to the proposed one.
_Avoid_: dictionary, term base

**Behind**:
Said of a translation whose original changed after it was translated.
_Avoid_: stale (that word is for register changes), outdated

**Intake**:
Reading a chat export and proposing register entries from it; nothing is written before the user confirms.
_Avoid_: import, ingest

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

**Schedule**:
An optional list of recipes and run times in the project config (`schedule`) that records what runs unattended.
_Avoid_: cron job, scheduled task, automated run, timer
