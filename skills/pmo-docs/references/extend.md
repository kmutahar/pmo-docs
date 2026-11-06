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
2. Add the type under `doc_types` in `pmo/config.yaml`: `title`, `template` (the file name), `name` (for example `"{period} - {title}.md"`), `generated_from` (every register the template reads, the same list as its `Reads:` comment), `when`, `regenerate`, and optionally `stale_days`. Set `generator: null` if drafted by the agent, and `publish: false` if it should stay unpublished.
3. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <id>` to confirm the template is found, then draft one (`references/draft.md`).

## Add or change a template

Copy the skill's template to `pmo/templates/` under the same file name and edit it. It replaces the default as a whole. Add `based_on: <type>@<version>` to its front matter. A change to headings or table columns raises `template_version` by one; documents made from the old version then warn until they are redrafted. Existing documents are not rewritten: list them and offer.
When the default template advances its version, `docs_audit.py` reports drift. Compare the override with the updated default, incorporate any improvements, and update `based_on`.

## Override or add a playbook

1. To override a default playbook, copy the skill's playbook from `references/<name>.md` to `pmo/playbooks/<name>.md`. Keep its front matter (`playbook_version: 1`) and add `based_on: <name>@<version>`.
2. When the skill's default playbook advances its version, `docs_audit.py` reports drift. Compare your override with the default, apply updates, and raise `based_on`.
3. To add a custom recipe: write `pmo/playbooks/<name>.md` with a `Reads:` line, inputs, numbered steps, and a reply. Use a name no skill playbook has (a playbook with the same name replaces it as an override). Add one line to `pmo/house-rules.md`: "For `<name>`, follow `pmo/playbooks/<name>.md`." House rules win over the routing table.

## Add a register

1. Create `pmo/registers/<name>.yaml`: a header comment and one list named `<name>`, one entry per line (`references/conventions.md`).
2. Add it under `registers` in the config: `file`, `view`, `prefix`, `fields`, and as needed `enums` (field to vocabulary name), `dates` and `closed`.
3. For a new status or level, add its list under `vocab`.
4. Run `render_views.py`. It checks the new register and writes its view.



## Change settings

Put only what differs in `pmo/config.yaml`: maps merge, lists replace, `null` removes a map entry. Typical changes are the priority order, the vocabularies, the paths and `stale_days`. Renaming a key that the skill's defaults define breaks the project's documents and templates: say so before doing it.

## Do not

- Edit `SKILL.md`, the skill's templates or its scripts.
- Put project facts (names, folders, statuses) anywhere but the config, the registers and the house rules.
