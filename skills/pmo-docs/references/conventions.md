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
| `documents` | `pmo/documents` | drafts and finished documents |
| `house_rules` | `pmo/house-rules.md` | the project's own rules |

## Where a document lives

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <type> [period] [--week] [--as-of YYYY-MM-DD] [--hashes]`. It prints `key: value` lines: the document path and whether it exists, the template path and whether it is the skill's or the project's, `template_version`, `based_on`, `generated_from`, `stale_days` and, with `--hashes`, `source_hashes`.

The file name comes from the doc type's `name` in the config. Tokens: `{title}` is the type's `title`; `{period}` is the month `YYYY-MM` (or the ISO week `YYYY-Www` with `--week`); `{date}` is the as-of date. With no period, the current month is used. Types named by `{date}` (change request, meeting minutes) need `--as-of` set to the date of the event. The ISO week starts on Monday.

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
| `based_on` | in a template override only: `<type>@<version>` |

## Registers

- A register file holds a single list named after it. Each entry is one line, a YAML flow mapping: `- { id: T-014, title: ..., owner: alice, status: in-progress, due: YYYY-MM-DD }`. A multi-line entry fails validation.
- Ids are the register's prefix and a number (`T-001`, `R-001`, `I-001`, `A-001`, `D-001`, `DEC-001`, `ACT-001`, `CR-001`, `MTG-001`, `M-001`, `P-001`, `O-001`, `B-001`, `TM-001`). The prefixes are in the config under `registers.<name>.prefix`. A new id is the highest existing number for the prefix plus one. The roster and capacity have no id.
- Owners are roster slugs. The roster register has one entry per person: `slug`, `name`, `role`.
- Statuses, severities, levels and similar values must come from the config's `vocab`. An empty vocab list accepts any value. `vocab.priority_order` lists the task priority levels, most urgent first.
- Dates are `YYYY-MM-DD`. The fields that hold dates are listed per register in the config (`dates`); the statuses that mean an entry is closed are `closed`.
- Every register has an optional `origin` field (`vocab.origin`): `stated` means the user or owner said it and `proposed` means the agent suggested it and it is not confirmed.
- To edit an entry, find its line with `grep -nE 'id: T-014[,}]' <register file>` and change that line only.
- After any edit run `render_views.py`. Views are deterministic (sorted, no timestamps), so after a merge conflict in a view the fix is to render again.

## Scripts

Run from the project root, or pass `--project DIR`. Every script answers `--help`, needs Python 3.10 or newer, and reads and writes UTF-8.

| Command | What it does | Exit codes |
|---|---|---|
| `python3 ${CLAUDE_SKILL_DIR}/scripts/setup.py [--name TEXT] [--manager TEXT] [--priority-order LIST]` | creates the config, house rules, empty registers and documents folder; never overwrites | 0 ok, 1 the new registers failed validation, 2 usage, a `schema_version` newer than the skill, or config paths that leave the project |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <type> [period] [--week] [--as-of DATE] [--hashes]` | paths and settings of one doc type; `--hashes` adds the `source_hashes` line Finish records | 0 ok, 2 usage, or a config the skill refuses |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py [--check]` | validates every register and writes the views; with `--check` it writes nothing and also fails when a view on disk is stale | 0 valid and current, 1 validation errors or stale views, 2 usage, a `schema_version` newer than the skill, or config paths that leave the project |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py [files]` | checks documents against their template (default: every document) | 0 clean (warnings allowed), 1 findings, 2 usage or a config the skill refuses |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py [--as-of DATE]` | front matter, stale, old and broken-link checks | 0 clean, 1 findings, 2 usage or a config the skill refuses |
| `python3 ${CLAUDE_SKILL_DIR}/scripts/overdue.py [--as-of DATE] [--days N]` | overdue tasks, actions and milestones, open risks and issues | 0 ok, 2 usage, or a config the skill refuses |

`structure_check.py` takes the checks from the winning template, never from the draft. It reports an error for a missing or out-of-order heading, changed table columns, a leftover `{{placeholder}}` or HTML comment, a repeated id in one table, or a declared check that fails (including one that names a section the document lacks). It warns about a missing or different `template_version`, extra `##` sections and empty tables.
