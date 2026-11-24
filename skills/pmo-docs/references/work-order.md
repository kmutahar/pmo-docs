---
playbook_version: 1
---

Reads: pmo/config.yaml (`doc_types.work-order`, `vocab.priority_order`), `where.py` output, registers `tasks`, `roster`.

# Recipe: work-order

Drafts a `work-order` document listing open tasks grouped by person, ordered by priority (from `vocab.priority_order`), then due date, then id. Draft only.

## Steps

1. **Find the path**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py work-order [--title TEXT]`. A second work order needs its own `--title`, and the same title goes to `generate.py` in step 2. `--title` names the file only: the document's own `{{title}}` (the piece of work, for example `Login`) is filled from the request. If the document exists, follow `references/draft.md` step 2.

2. **Generate**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/generate.py work-order`; when the request names tasks, add `--task ID` for each (and the same `--title TEXT` as in step 1 when you gave one), so the list, lead and due date cover only those. Fill any remaining prose sections (`Purpose`, `Scope`, `Acceptance`) from the request or registers without inventing facts (`SKILL.md`, Safety rule 2).

3. **Check**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py "<file>"`.

4. **Reply**
   Report the document path, open task counts per person, the number of unowned tasks (if any), the number of undated tasks (if any), open questions, and the next step: review, edit, then Finish (`references/finish.md`).

## Do not

- Break a rule in `SKILL.md`: Working rules "Existing documents are hand-edited", "Finish only when asked".
- Finish, publish, send or commit.
