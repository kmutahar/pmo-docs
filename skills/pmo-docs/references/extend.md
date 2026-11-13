---
playbook_version: 1
---

Reads: pmo/config.yaml, pmo/house-rules.md, the skill's `assets/config.default.yaml` and `assets/templates/` (as models).

# Extend

Change what the project produces without editing the skill. Every change below is a file in the project's `pmo/` folder. The lookup and merge rules are in `SKILL.md` (House rules and lookup). Show the planned change and wait for a yes before writing (`SKILL.md`, Safety rule 3: a change to the config, a template or a playbook is always shown first).

## Check after any change

Run `render_views.py --check`, then `structure_check.py` and `docs_audit.py`. Report what they say.

## Add a doc type

1. Copy a similar template from the skill into `pmo/templates/<file>.md`. Front matter: `title`, `type` (the new id), `project`, `manager`, `template_version: 1`, `period` when the document is periodic, `status`, `last_updated`, and `checks:` if wanted (the kinds are listed at the top of `scripts/structure_check.py`). One `#` heading, the `##` sections, the last one `## Open questions`. A comment `<!-- Reads: ... -->` naming the registers it reads.
2. Add the type under `doc_types` in `pmo/config.yaml`: `title`, `template` (the file name), `name` (for example `"{period} - {title}.md"`), `generated_from` (every register the template reads, the same list as its `Reads:` comment), `when`, `regenerate`, and optionally `stale_days`. Set `generator: null` if drafted by the agent, and `publish: false` if it should stay unpublished.
3. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <id>` to confirm the template is found, then draft one (`references/draft.md`).

## Add or change a template

Copy the skill's template `${CLAUDE_SKILL_DIR}/assets/templates/<type>.md` to `pmo/templates/` under the same file name and edit it. It replaces the default as a whole. Add `based_on: <type>@<version>` to its front matter. A change to headings or table columns raises `template_version` by one; documents made from the old version then warn until they are redrafted. Existing documents are not rewritten: list them and offer.
When the default template advances its version, `docs_audit.py` reports drift. Compare the override with the updated default, incorporate any improvements, and update `based_on`.

## Override or add a playbook

1. To override a default playbook, copy the skill's playbook from `${CLAUDE_SKILL_DIR}/references/<name>.md` to `pmo/playbooks/<name>.md`. Keep its front matter (`playbook_version: 1`) and add `based_on: <name>@<version>`.
2. When the skill's default playbook advances its version, `docs_audit.py` reports drift. Compare your override with the default, apply updates, and raise `based_on`.
3. To add a custom recipe: write `pmo/playbooks/<name>.md` with a `Reads:` line, inputs, numbered steps, and a reply. Use a name no skill playbook has (a playbook with the same name replaces it as an override). Add one line to `pmo/house-rules.md`: "For `<name>`, follow `pmo/playbooks/<name>.md`." House rules win over the routing table.

## Add a stack file

1. To support a new framework or technology, write `pmo/playbooks/stacks/<stack>.md` with front matter `playbook_version: 1`, followed by `Detected by: ...` and `Checked against: ...`, a `#` title, and the six standard `##` headings in order: `Routes, pages or screens`, `Data models`, `Permissions and auth`, `Config and environments`, `Tests`, `List the API live`.
2. To override a shipped stack file, copy `references/stacks/<stack>.md` to `pmo/playbooks/stacks/<stack>.md` and record `based_on: stacks/<stack>@<version>` in its front matter.
3. Add the stack slug to `technical.stacks` in `pmo/config.yaml`.

## Add a register

1. Create `pmo/registers/<name>.yaml`: a header comment and one list named `<name>`, one entry per line (`references/conventions.md`).
2. Add it under `registers` in the config: `file`, `view`, `prefix`, `fields`, and as needed `enums` (field to vocabulary name), `dates` and `closed`.
3. For a new status or level, add its list under `vocab`.
4. Run `render_views.py`. It checks the new register and writes its view.

To add a field to an existing register, set `registers.<name>.fields` in the config. It is a list, so it replaces the default: repeat every field of the default list from `${CLAUDE_SKILL_DIR}/assets/config.default.yaml` and add the new one. The register's `enums` and `dates` are maps, so give only the new entries. Run `render_views.py`.



## Change settings

Put only what differs in `pmo/config.yaml`: maps merge, lists replace, `null` removes a map entry. Typical changes are the priority order, the vocabularies, the paths and `stale_days`. Renaming a key that the skill's defaults (`${CLAUDE_SKILL_DIR}/assets/config.default.yaml`) define breaks the project's documents and templates: say so before doing it.

## Add a language

1. Add the language to `languages` in `pmo/config.yaml` (codes are 2 or 3 letters; quote one YAML would read as something else, such as `no`). Existing documents are not translated until you ask.
   ```yaml
   languages:
     translations: [xx]
     xx: { label: XX, dir: rtl, glossary: pmo/data/glossary-xx.md }
   ```
2. `glossary` is a Markdown file inside the project; the proposed list sits next to it as `<name>.proposed.md`. `digits`, `connectors` and `separators` are optional (`references/conventions.md`).
3. To change when or where a type is translated, set `doc_types.<type>.translate` (`in-period` or `after-close`) and `doc_types.<type>.translations` (a list that replaces `languages.translations`; `[]` means none).
4. Run `render_views.py`; it checks the new keys. Then translate with `references/translate.md`.

## Do not

- Edit `SKILL.md`, the skill's templates or its scripts.
- Put project facts (names, folders, statuses) anywhere but the config, the registers and the house rules.
