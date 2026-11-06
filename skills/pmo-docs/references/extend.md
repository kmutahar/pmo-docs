---
playbook_version: 1
---

Reads: pmo/config.yaml, pmo/house-rules.md, the skill's `assets/config.default.yaml` and `assets/templates/` (as models).

# Extend

Change what the project produces without editing the skill. Every change below is a file in the project's `pmo/` folder. The lookup and merge rules are in `SKILL.md` (House rules and lookup). Show the planned change and wait for a yes before writing (`SKILL.md`, Safety rules).

## Check after any change

Run `render_views.py --check`, then `structure_check.py` and `docs_audit.py`. Report what they say.

## Add a doc type

1. Copy a similar template from the skill into `pmo/templates/<file>.md`. Front matter: `title`, `type` (the new id), `project`, `manager`, `template_version: 1`, `period` when the document is periodic, `status`, `last_updated`, and `checks:` if wanted (the kinds are listed at the top of `scripts/structure_check.py`). One `#` heading, the `##` sections, the last one `## Open questions`. A comment `<!-- Reads: ... -->` naming the registers it reads.
2. Add the type under `doc_types` in `pmo/config.yaml`: `title`, `template` (the file name), `name` (for example `"{period} - {title}.md"`), `generated_from` (every register the template reads, the same list as its `Reads:` comment) and optionally `stale_days`.
3. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <id>` to confirm the template is found, then draft one (`references/draft.md`).

## Add or change a template

Copy the skill's template to `pmo/templates/` under the same file name and edit it. It replaces the default as a whole. Add `based_on: <type>@<version>` to its front matter. A change to headings or table columns raises `template_version` by one; documents made from the old version then warn until they are redrafted. Existing documents are not rewritten: list them and offer.

## Add a register

1. Create `pmo/registers/<name>.yaml`: a header comment and one list named `<name>`, one entry per line (`references/conventions.md`).
2. Add it under `registers` in the config: `file`, `view`, `prefix`, `fields`, and as needed `enums` (field to vocabulary name), `dates` and `closed`.
3. For a new status or level, add its list under `vocab`.
4. Run `render_views.py`. It checks the new register and writes its view.

## Add a recipe

A recipe is a named request with fixed inputs that produces a draft and may edit registers; it never publishes or sends.

1. Write `pmo/playbooks/<name>.md` in the shape of the skill's recipes: a `Reads:` line, the inputs, numbered steps, the draft it produces, a reply.
2. Add one line to `pmo/house-rules.md`: "For `<name>`, follow `pmo/playbooks/<name>.md`." House rules win over the skill's routing table.

## Change settings

Put only what differs in `pmo/config.yaml`: maps merge, lists replace, `null` removes a map entry. Typical changes are the priority order, the vocabularies, the paths and `stale_days`. Renaming a key that the skill's defaults define breaks the project's documents and templates: say so before doing it.

## Do not

- Edit `SKILL.md`, the skill's templates or its scripts.
- Put project facts (names, folders, statuses) anywhere but the config, the registers and the house rules.
