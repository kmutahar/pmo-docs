---
playbook_version: 1
---

Reads: pmo/config.yaml (doc_types.overdue-report), `where.py` output, `overdue.py` output, registers `tasks`, `milestones`, `actions`, `risks`, `issues`.

# Recipe: overdue-report

Run as `overdue-report [--as-of YYYY-MM-DD]`. Produces a draft `overdue-report` for the current month (one file per month, so a second run refreshes it as `references/draft.md` step 2 says). Draft only.

## Steps

1. **Find the path**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py overdue-report [--as-of YYYY-MM-DD]`.

2. **Validate and collect**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check`, then `python3 ${CLAUDE_SKILL_DIR}/scripts/overdue.py [--as-of YYYY-MM-DD]`. Stop on register errors.

3. **Draft**
   Put the tool's tables into the template section by section and add nothing beside them except to replace each owner slug with the roster name (`references/draft.md` steps 4 to 8). Open tasks with no due date go in Open questions, counted.
   If most open tasks have no due date, say so first and recommend setting dates for the most urgent priority with the user (`references/track.md`). Never infer a date.

4. **Suggest next steps**
   At most five, each naming an id, a person and what to ask them ("ask <owner name> whether `T-4` is unblocked"). For a risk, the step is its mitigation.

5. **Reply**
   Path, the counts (overdue, undated), the three most urgent items and the recommended action. The user says when it is ready to Finish.

## Do not

- Infer a due date or change a status.
- Finish, publish, send or commit.
