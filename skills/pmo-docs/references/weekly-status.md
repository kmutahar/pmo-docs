---
playbook_version: 1
---

Reads: pmo/config.yaml (doc_types.status-report), pmo/house-rules.md, `where.py` output, registers `tasks`, `milestones`, `risks`, `issues`, `changes`, `actions`, `decisions`, `teams`; the previous status report.

# Recipe: weekly-status

Run as `weekly-status [--week YYYY-Www]`. Produces a draft `status-report` for one week. Draft only.

## Steps

1. **Find the week and the paths**
   With no `--week`, use the current week. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py status-report [YYYY-Www] --week`. Read the `window` line (`YYYY-MM-DD..YYYY-MM-DD`) from its output (`SKILL.md`, Documents). If the document exists, follow `references/draft.md` step 2.
   Find the previous report in `paths.documents`: the status report of the week before, or the latest one. With none, say "first report, no comparison" and skip deltas.


2. **Validate the registers**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check`. Stop on errors.

3. **Count the period's tasks**
   Count only tasks whose `period` is the month that holds at least 4 of the window's 7 days (the month of its fourth day; a task with no `period` counts when its `due` falls in the window). Done tasks of earlier periods appear on one line ("completed before <period>: N") and stay out of totals, percentages and deltas.

4. **Git evidence (optional)**
   If the user names folders that hold work, read their history for the window (`references/git.md`) and say "local history as of <date>". With none, write in Notes on data that no git evidence was used.
   Match commits to tasks by title, keyword and touched path. Show a list: task id, commits, the status the history suggests. Change no status; update only the entries the user confirms (`references/track.md`).

5. **Compute**
   Totals and percentages per priority level and per team; blocked and overdue tasks (`python3 ${CLAUDE_SKILL_DIR}/scripts/overdue.py --as-of <last day of the window>`); milestones due in the next 14 days; the change since the previous report. A done task is new when its id is not in the previous report's Completed section.

6. **Set the RAG** as defined in `references/conventions.md` (evaluated with `pmo_common.rag`) and state the rule in Notes on data. A house rule can replace this rule.

7. **Draft**
   If `doc_types.status-report.generator` is `true` (when a house rule replaces the RAG rule, recompute Overall and its reason and the RAG column of Progress by priority by that rule, and change the RAG line in Notes on data), run `python3 ${CLAUDE_SKILL_DIR}/scripts/generate.py status-report [YYYY-Www] --week` and fill only what was left (prose placeholders, `{{comment}}`-style cells, agent sections). Otherwise fill the status-report template from steps 3 to 6 and write it to the path from step 1 (`references/draft.md` steps 4 to 8). Blockers are the blocked tasks plus the open items that need someone's decision.


8. **Reply**
   Path, overall RAG and its reason, the three numbers that matter, the status changes waiting for the user's confirmation, and the next step: edit it, then say it is ready and Finish (`references/finish.md`).

## Do not

- Change a status from git history.
- Finish, publish, send or commit.
