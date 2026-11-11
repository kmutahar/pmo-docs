---
playbook_version: 1
---

Reads: pmo/config.yaml (paths, registers, doc_types).

# Conventions

Formats and tools shared by the playbooks. Behaviour rules are in `SKILL.md`; this file holds only formats and facts.

## Folders

All paths come from the config (`paths`), relative to the project root. Defaults:

| Key | Default | Holds |
|---|---|---|
| `registers` | `pmo/registers` | one YAML file per register |
| `views` | `pmo/views` | generated Markdown views, committed, never edited by hand |
| `templates` | `pmo/templates` | the project's own templates (overrides) |
| `playbooks` | `pmo/playbooks` | the project's own playbooks (overrides) |
| `documents` | `pmo/documents` | drafts and finished documents |
| `house_rules` | `pmo/house-rules.md` | the project's own rules |

Templates and playbooks follow the lookup rule: the project's file in `paths.templates` or `paths.playbooks` wins over the skill's default. Playbook lookup includes subfolders such as `stacks/`: `<paths.playbooks>/stacks/<stack>.md` overrides `references/stacks/<stack>.md`.

## Where a document lives

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <type> [period] [--week] [--as-of YYYY-MM-DD] [--hashes] [--title TEXT] [--lang CODE]`. It prints `key: value` lines: the document path and whether it exists, the template path and whether it is the skill's or the project's, `template_version`, `based_on`, `drift`, `generated_from`, `stale_days`, `window` (`YYYY-MM-DD..YYYY-MM-DD`), `translations` (the codes the type translates into, or `none`), `translate` (`in-period` or `after-close`) and, with `--hashes`, `source_hashes`. With `--lang CODE`, `document` is the translation's path and these lines follow it: `original`, `original_exists`, `translation_of` (the value for the front matter, quoted), `lang`, `dir`, `glossary`, `glossary_proposed` (`none` when not configured); `--hashes` then prints `source_hash` (the hash of the original's body, or `none`) instead of `source_hashes`. A code the type does not translate into exits 2.

The file name comes from the doc type's `name` in the config. Tokens: `{title}` is the type's `title` (or overridden by `--title`); `{period}` is the month `YYYY-MM` (or the week `YYYY-Www` with `--week`, starting on `project.week_start`); `{date}` is the as-of date. With no period, the current month is used. Types named by `{date}` (change request, meeting minutes) need `--as-of` set to the date of the event. A week starts on `project.week_start` (default Monday) and is named by the ISO week of its fourth day.


## Front matter

Every document starts with YAML front matter.

| Key | Meaning |
|---|---|
| `title` | the document title |
| `type` | the doc type id; the checks are chosen by it |
| `project`, `manager` | from the config |
| `period` | `YYYY-MM` or `YYYY-Www`; on every type whose template has it (periodic types and the roadmap) |
| `template_version` | copied from the template |
| `status` | `draft` or `finished` |
| `last_updated` | `YYYY-MM-DD` |
| `checks` | the template's checks; present in drafts, removed by Finish |
| `source_hashes` | written by Finish: register name to a quoted 8-character hash |
| `code_ref` | documents read from code: the commit hash the code was read at (quoted) |
| `based_on` | in a template override only: `<type>@<version>` |
| `lang`, `dir`, `translation_of`, `source_hash` | a translation only: its language code, `ltr` or `rtl`, the original's path relative to `paths.documents`, and the 8-character hash of the original's body when it was translated (quoted). A translation has no `checks` and no `source_hashes`. |

A translation is a file next to its original, named `<name>.<lang>.md` (for example `2026-03 - Status report.xx.md`). It is a translation when its front matter has `translation_of`. Templates do not carry these keys.

## Registers

- A register file holds a single list named after it. Each entry is one line, a YAML flow mapping: `- { id: T-014, title: ..., owner: alice, status: in-progress, due: YYYY-MM-DD }`. A multi-line entry fails validation.
- Ids are the register's prefix and a number (`T-001`, `R-001`, `I-001`, `A-001`, `D-001`, `DEC-001`, `ACT-001`, `CR-001`, `MTG-001`, `M-001`, `P-001`, `O-001`, `B-001`, `TM-001`, `REQ-001`, `TST-001`, `ENV-001`, `PERM-001`). The prefixes are in the config under `registers.<name>.prefix`. A new id is the highest existing number for the prefix plus one. The roster and capacity have no id.
- Owners are roster slugs. The roster register has one entry per person: `slug`, `name`, `role`.
- Statuses, severities, levels and similar values must come from the config's `vocab`. An empty vocab list accepts any value. `vocab.priority_order` lists the task priority levels, most urgent first.
- Credential-like strings (a password, token, key or a link with a password) in any field are a validation error; the message names the entry and field, never the text.
- Dates are `YYYY-MM-DD`. The fields that hold dates are listed per register in the config (`dates`); the statuses that mean an entry is closed are `closed`.
- Every register has an optional `origin` field (`vocab.origin`): `stated` means the user or owner said it and `proposed` means the agent suggested it and it is not confirmed.
- To edit an entry, find its line with `grep -nE 'id: T-014[,}]' <register file>` and change that line only.
- After any edit run `render_views.py`. Views are deterministic (sorted, no timestamps), so after a merge conflict in a view the fix is to render again.

## Config keys

- `project.week_start`: day of the week a working week starts (`monday`, `tuesday`, ..., `sunday`; default `monday`).
- `domain.lifecycle_entity`: entity name whose life cycle is described by `entity-lifecycle` (default `null`).
- `domain.roles`: list of permission roles as named in code (for example `[admin, editor, viewer]`).
- `technical.stacks`: list of stack names the project code is built on (such as `[nextjs]`).
- `technical.consumers`: list of systems or teams that call the API, one section each in `integration-guide`.
- `registers.<name>.refs`: mapping of register field names to target register names (e.g. `tests: tests`). Validation checks that referenced IDs exist in the target register when that register exists.
- `registers.tasks.done`: status values marking tasks as done (default `[done]`).
- `registers.tasks.blocked`: status values that count as blocked (default `[blocked]`).
- `registers.tasks.active`: status values marking tasks currently active (default `[in-progress]`).
- `registers.changes.accepted`: status values marking change requests as accepted (default `[approved, implemented]`).
- `languages`: `draft` (the language documents are written in, default `en`), `translations` (codes of the other languages, default none) and one block per code with `label`, `dir` (`ltr` or `rtl`) and optionally `glossary` (approved term list, a `.md` file inside the project; the proposed list is `<stem>.proposed.md` next to it), `digits` (ten characters for 0 to 9), `connectors` (words for `of`, `to`, `and` between two numbers) and `separators` (decimal or thousands marks). A missing block means English only. Quote a code YAML would read as something else (`no`, `on`).
- `doc_types.<type>.translate`: `in-period` (default) or `after-close`, when translations are made. `doc_types.<type>.translations`: codes that replace `languages.translations` for the type; `[]` means none.
- `registers.tasks` field `done_on` (a date, optional): when a task was finished or dropped.
- `doc_types.<type>.generator`: `true` to use `generate.py` to pre-fill the document, `false` or `null` to draft via agent. Generators write English only: `generate.py` exits 2 when `languages.draft` is not `en`.
- `doc_types.<type>.publish`: `false` excludes the doc type from publishing (e.g. internal audit reports).
- `doc_types.<type>.when`: text explaining the event or rhythm when the document is made.
- `doc_types.<type>.regenerate`: guidance on when and how to regenerate the document.
- `publish.mode`: `none` (default), `folder` (folder inside project), or `repo` (root of another local git repo).
- `publish.path`: publish target path relative to project root or absolute (`repo` mode).
- `publish.url`: optional web URL prefix used when printing published links.

## Views and catalogue

- Register views (`pmo/views/<name>.md`) summarize each register.
- The catalogue view (`pmo/views/catalogue.md`) is rendered by `render_views.py` from `doc_types` in `pmo/config.yaml`. It lists doc type, title, made by (`generator` or `agent`), when to make it, regenerate guidance, stale period, and publish status.

## RAG status

Status reports show RAG (Red / Amber / Green) as `pmo_common.rag` computes it (a house rule can replace it; see `weekly-status.md`). Red and Amber use the vocab positions `vocab.rag[2]` and `[1]`:
- `Red`: a top-priority task (`vocab.priority_order[0]`) is blocked or overdue, a milestone is overdue, or three or more tasks are blocked or overdue.
- `Amber`: any task is blocked or overdue, an open issue has one of the two highest severities, an open risk has the highest impact, or a milestone is due within 7 days.
- `Green`: none of these.

## Scripts

Run from the project root, or pass `--project DIR`. Every script answers `--help`, needs Python 3.10 or newer, and reads and writes UTF-8.

| Command | What it does | Exit codes |
|---|---|---|
| `python3 ${CLAUDE_SKILL_DIR}/scripts/setup.py [--name TEXT] [--manager TEXT] [--priority-order LIST] [--week-start DAY]` | creates the config, house rules, empty registers and documents folder; never overwrites | 0 ok, 1 the new registers failed validation, 2 usage, a `schema_version` newer than the skill, or config paths that leave the project |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <type> [period] [--week] [--as-of DATE] [--hashes] [--title TEXT] [--lang CODE]` | paths and settings of one doc type; `--hashes` adds the `source_hashes` line Finish records; `--lang` gives a translation's paths and `source_hash` | 0 ok, 2 usage, or a config the skill refuses |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/generate.py <type> [period] [--week] [--as-of DATE] [--stdout]` | pre-fills a document from registers for generator doc types; never overwrites | 0 ok, 1 validation errors, 2 usage, invalid doc type or a non-English draft language, 3 the document already exists |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py [--check]` | validates every register and writes the views; with `--check` it writes nothing and also fails when a view on disk is stale | 0 valid and current, 1 validation errors or stale views, 2 usage, a `schema_version` newer than the skill, or config paths that leave the project |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/publish.py [--apply] [--overwrite REL]... [--include REL]... [--as-of DATE]` | lists candidates or copies finished documents into `publish.path`; dry run without `--apply` | 0 ok / dry run clean, 1 uncopied conflict or stale documents remaining, 2 usage or invalid target |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py [files]` | checks documents against their template (default: every document) | 0 clean (warnings allowed), 1 findings, 2 usage or a config the skill refuses |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/parity_check.py [files]` | checks that a translation has the same headings, tables, ids and numbers as its original (default: every translation) | 0 all match or none found, 1 a difference or a pair that cannot be compared, 2 usage or a config the skill refuses |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py [--as-of DATE]` | front matter, stale, old, broken-link, template/playbook drift, translation-behind and parity checks | 0 clean, 1 findings, 2 usage or a config the skill refuses |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/overdue.py [--as-of DATE] [--days N]` | overdue tasks, actions and milestones, open risks and issues | 0 ok, 2 usage, or a config the skill refuses |


`structure_check.py` takes the checks from the winning template, never from the draft. It reports an error for a missing or out-of-order heading, changed table columns, a leftover `{{placeholder}}` or HTML comment, a repeated id in one table, or a declared check that fails (including one that names a section the document lacks). It warns about a missing or different `template_version`, extra `##` sections and empty tables.
