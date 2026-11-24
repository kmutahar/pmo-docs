---
playbook_version: 1
---

Reads: pmo/config.yaml (`languages`, `doc_types`), `where.py --lang` output, the original, the existing translation, the glossary.

# Translate

The rules for translations live in `SKILL.md` (Translations) and `references/conventions.md`; this playbook gives the steps to translate a document or bring an existing translation back in step.

## Steps

1. **Identify the document, period and language**
   Ask when any is unclear. A language not in the type's `translations` goes to `references/extend.md` first.

2. **Find the paths**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <type> [period] --lang <code> --hashes`. Note `document`, `original`, `translation_of`, `dir`, `glossary`, `names` and `source_hash`. The original must exist. If it is a draft, the translation can be drafted but not finished.

3. **Decide the case**
   - No translation file: translate (step 5).
   - Translation exists, `status: finished` and `source_hash` equals the printed one: say it is up to date and stop.
   - Translation exists and differs: bring it back in step (step 4). Never overwrite a translation the user edited by hand: show the difference and ask (`SKILL.md`, Working rules).

4. **Bring back in step**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/parity_check.py "<translation>"`; its messages name the sections that differ in structure, ids or numbers. Read the original and the translation side by side for sections whose wording changed with no id or number change. List the sections you will update and wait for a yes. Update those sections only. Leave the user's own wording in the others.
   When a reviewer gives feedback on a translation: if it is wording or phrasing only (same facts, numbers, dates and structure), edit only the translation; if it changes facts, numbers, dates or meaning, propose the change to the original (and the underlying register when it is register data), wait for a yes, update the original first, then bring the translation back in step.

5. **Read the glossaries**
   Read the glossary if it exists: one Markdown file with an `## Approved` and a `## Proposed` section. Approved rows are a table `| ID | Term | Translation | Note |`; the ID is `G-001`, `G-002` and so on, the term is in the draft language. Use the Approved translation for every listed term, exactly, for headings, column names and labels too. A domain term that is not listed in either section: translate it consistently inside this document and append one row to the Proposed table `| ID | Term | Translation | Seen in | Date |`. A term already under Proposed is used as proposed and not added again. The new ID is the next number after the highest ID in the file; an ID is never reused, and a row the user moves up to Approved keeps its ID, so teams can review by ID. If the file is missing, create it (and the folder) with both sections and their table headers. Only append rows under Proposed with a targeted edit: never change, move or delete another line, and never add under Approved. The file may also have a `## Do not translate` section, a bullet list of terms (product and brand names, code words) that stay as written in the draft language: keep each one untranslated in the body, headings and labels, do not add it to Proposed, and never edit the section. `docs_audit.py` and `parity_check.py` accept it.

6. **Write the translation**
   Front matter is the original's, minus `checks` and `source_hashes`, with `title` translated and `lang`, `dir`, `translation_of`, `source_hash` added (the values `where.py` printed; if it cannot run, leave `source_hash` out and say so); `status: draft`; `last_updated` today.
   Body: the same headings in the same order and levels, the same tables (same columns and rows, in the same order), the same fields and checkboxes. Translate the heading text, the column names and the field labels (`Status`, `Date`) with the glossary; only the structure is compared, not the words. Keep the same ids (in backticks where the original has them), the same numbers (written with the language's digits when the config has `digits`), the same dates (`YYYY-MM-DD`), links, paths and code. Translate the words `not set`, `not provided`, `not recorded`, `None` and the `Open questions` section consistently with the glossary. Register text that appears in the body (roster names and roles, task titles, any other field) is used as the Approved entry of the names file says (`names` from `where.py`: `approved:` and `proposed:`, each register -> id (the roster's slug) -> field -> text). Text not in the file: a person's name is transliterated or kept as the roster has it, anything else is translated consistently; either way add one entry under `proposed:` for each new id and field (targeted edit, never change `approved:`), and create the file with both keys if the config names it and it is missing. With no `names` file the roster names stay as they are and nothing is added. Add nothing the original does not say; leave nothing out. Keep the original's comments out of the translation.

7. **Check**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/parity_check.py "<file>"` and `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py "<file>"`. Fix every difference by changing the translation, never the original. Do not finish while parity reports anything.

8. **Finish**
   Finish only when the user says so, or says yes when you ask. Do it as `SKILL.md` defines it for a translation (Finish, step 8). The original must be finished first.

9. **Reply**
   Path, parity and structure results, the terms and names added under Proposed (counts and files), what is left for the user (move rows up to Approved, review the translation), and that the user commits it.

## Do not

- Break a rule in `SKILL.md`: Working rules "Finish only when asked", "Existing documents are hand-edited".
- Translate unasked.
- Edit the original.
- Invent or drop a fact.
- Write to the approved glossary.
- Finish before the original is finished.
- Publish, send or commit.

## Settings and scripts

- Config keys `languages` and `doc_types.<type>.translate` / `translations`: `references/conventions.md` (Config keys). Finish step 8 in `SKILL.md` says when translation is offered.
- `parity_check.py`: compares a translation with its original (headings, tables, ids, numbers, list items, ticked boxes).
- `docs_audit.py`: reports a translation that is behind its original checks parity and checks glossary IDs.
