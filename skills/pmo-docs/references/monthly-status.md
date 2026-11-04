Reads: pmo/config.yaml (doc_types.status-report), pmo/house-rules.md, `where.py` output, registers `tasks`, `milestones`, `risks`, `issues`, `changes`, `actions`, `decisions`, `teams`; the month's weekly status reports.

# Recipe: monthly-status

Run as `monthly-status [--period YYYY-MM]`. Produces a draft `status-report` for one month. Draft only.

## Steps

1. **Find the period and the paths**
   With no `--period`, use the current month. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py status-report [YYYY-MM]`. If the document exists, follow `references/draft.md` step 2.

2. **Do the weekly steps**
   Follow `references/weekly-status.md` steps 2 to 6 with the window set to the whole month (to today when the month is still running). The previous report is the one for the month before.
   Tasks carried over by `month-start` belong to the new month; earlier-period done tasks stay on the one history line.

3. **Add the monthly view** to the matching sections of the template, with no new sections:
   - Trend: the done and total figures of the month's weekly reports, as one line in Summary.
   - Progress by priority: one row per priority level; in each Comment, the main change since the previous report.
   - Milestones: each milestone due in the month, with its result.
   - Decisions and changes: approved changes and decisions dated in the month.
   - Risks and issues: opened, closed and still open in the month.
   - Forecast, as one line in Summary: tasks still open against the weeks left, flagged when the open count is more than the pace of recent weeks would finish. Label it an estimate and give the method in Notes on data.

4. **Draft**
   Fill the template and write it to the path from step 1 (`references/draft.md` steps 4 to 8).

5. **Reply**
   As in `references/weekly-status.md`. If the month has ended, suggest the next steps: draft `delivery-report`, then `retrospective`, then run `month-start`.

## Do not

- Change a status from git history.
- Finish, publish, send or commit.
