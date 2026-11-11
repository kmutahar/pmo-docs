---
playbook_version: 1
---

Reads: the draft, pmo/config.yaml (doc_types.<type>.generated_from), `where.py` output, the registers named in `generated_from` (only to see when they last changed).

# Finish

Turn a draft the user has approved into a finished document. The Finish steps are defined in `SKILL.md`; this playbook decides when to run them.

## Steps

1. **Find the draft**
   Use the document the user named. If none is named, list the documents under `paths.documents` with `status: draft` and ask which. Finish only the ones named ("all" means every draft).
   A document that is already finished: say so and stop, unless `docs_audit.py` reports it stale, in which case offer a new draft (`references/draft.md`).

2. **Check the registers have not moved**
   Compare the register hashes recorded in the document's front matter (`source_hashes`) against current hashes from `where.py --hashes`. If any recorded hash differs, tell the user what changed and ask whether to refresh the draft first. If the document has no recorded `source_hashes` (a draft being finished for the first time), do not compare file modification dates or git commit dates: a fresh clone or an older period draft always looks newer than its file dates. Finish records the registers as they are now. Never refresh over the user's edits.

3. **Look at the open questions**
   If the draft still has open questions, list them and ask whether to finish anyway. They stay in the document.

4. **Finish**
   Do the Finish steps in `SKILL.md`, in order, on the one document.

5. **Translations**
   `where.py` prints `translations` and `translate` for the type. Follow `SKILL.md`, Finish, step 8: skip, or ask once. A translation is finished only after its original.

6. **If a check fails**
   Fix what is mechanical (a leftover comment, a placeholder, a heading's spelling). A failure that needs a decision or a fact goes back to the user. Do not set `status: finished` until `structure_check.py` reports no errors.

7. **Reply**
   Give the path, the result of the checks (warnings included), the registers whose hashes were recorded, the translations made or skipped, and that the user commits it when they choose.

## Do not

- Publish, send or commit.
- Regenerate content the user wrote.
