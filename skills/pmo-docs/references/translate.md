---
playbook_version: 1
---

Reads: pmo/config.yaml (`languages`, `doc_types`), `where.py --lang` output, the original, the existing translation, the approved and proposed glossaries.

# Translate

The rules for translations live in `SKILL.md` (Translations) and `references/conventions.md`; this playbook gives the steps to translate a document or bring an existing translation back in step.

## Steps

1. **Identify the document, period and language**
   Ask when any is unclear. A language not in the type's `translations` goes to `references/extend.md` first.

2. **Find the paths**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <type> [period] --lang <code> --hashes`. Note `document`, `original`, `translation_of`, `dir`, `glossary`, `glossary_proposed` and `source_hash`. The original must exist. If it is a draft, the translation can be drafted but not finished.

3. **Decide the case**
   - No translation file: translate (step 5).
   - Translation exists, `status: finished` and `source_hash` equals the printed one: say it is up to date and stop.
   - Translation exists and differs: bring it back in step (step 4). Never overwrite a translation the user edited by hand: show the difference and ask (`SKILL.md`, Working rules).

4. **Bring back in step**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/parity_check.py "<translation>"`; its messages name the sections that differ in structure, ids or numbers. Read the original and the translation side by side for sections whose wording changed with no id or number change. List the sections you will update and wait for a yes. Update those sections only. Leave the user's own wording in the others.

5. **Read the glossaries**
   Read the approved glossary if it exists (a Markdown table `| Term | Translation | Note |`, first column in the draft language). Use its translation for every listed term, exactly. A domain term that is not listed: translate it consistently inside this document and append one row to the proposed file `| Term | Proposed translation | Seen in | Date |` unless the term is already there. Create the proposed file with its header and the folder if missing. Never write to the approved file.

6. **Write the translation**
   Front matter is the original's, minus `checks` and `source_hashes`, with `title` translated and `lang`, `dir`, `translation_of`, `source_hash` added (the values `where.py` printed; if it cannot run, leave `source_hash` out and say so); `status: draft`; `last_updated` today.
   Body: the same headings in the same order and levels, the same tables (same columns and rows, in the same order), the same ids (in backticks where the original has them), the same numbers (written with the language's digits when the config has `digits`), the same dates (`YYYY-MM-DD`), links, paths and code. Translate the words `not set`, `not provided`, `not recorded`, `None` and the `Open questions` section consistently with the glossary. Names from the roster stay as the roster has them. Add nothing the original does not say; leave nothing out. Keep the original's comments out of the translation.

7. **Check**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/parity_check.py "<file>"` and `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py "<file>"`. Fix every difference by changing the translation, never the original. Do not finish while parity reports anything.

8. **Finish**
   Finish only when the user says so, or when Finish asked and was told yes (`SKILL.md`, Finish, step 8). The original must be finished. Set `source_hash` to the value `where.py --lang --hashes` prints now, remove comments, run `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py`, set `status: finished` and `last_updated`.

9. **Reply**
   Path, parity and structure results, the terms added to the proposed glossary (count and file), what is left for the user (move terms to the approved glossary, review the translation), and that the user commits it.

## Do not

- Translate unasked.
- Edit the original.
- Invent or drop a fact.
- Write to the approved glossary.
- Finish before the original is finished.
- Publish, send or commit.
