Reads: pmo/config.yaml (registers, doc_types), pmo/house-rules.md, registers `tasks`, `milestones`, `priorities` (goals), `capacity`, `risks`, `assumptions`, `dependencies`, `actions`.

# Recipe: month-start

Run as `month-start [--period YYYY-MM]`. Sets up the registers and draft documents for a new month. Draft only.

## Steps

1. **Confirm the period**
   Default is the current month (the new month); the closing month is the one before it. For a later month, the user passes `--period`. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py delivery-report <closing month>`. If that delivery report does not exist, say so and offer to draft it first; do not block.

2. **Note the baseline**
   Git history is the record of the closing month, so make no copies. Run `git status -sb` and `git log -1 --oneline` (read-only, `references/git.md`) and tell the user whether registers have uncommitted changes.

3. **Show the carry-over**
   List, and change nothing yet:
   - Tasks not `done` or `dropped`, counted by priority level. Carrying them over keeps the id, sets `period` to the new month and adds `carried from <old>` to `notes`. Done and dropped tasks stay as history.
   - Milestones of the closing or an earlier month that are not done. Ask about each; moving a due date is a change request (`references/govern.md`). Never move or close one silently.
   - Open risks, assumptions, dependencies and actions: they stay as they are.
   Wait for the user's yes.

4. **Ask for the new month's inputs**
   One short set of questions, defaults shown (at most four per call): the objective; which goals to keep, drop or change; new tasks; leave and capacity; milestone dates; task due dates. A change to carried work's scope, priority level, owner or date is a change request unless the user says it is the new plan.

5. **Update the registers**
   Apply the carry-over and the answers one line at a time (`references/track.md`): the tasks, new milestones with the new `period`, goals kept, dropped or changed (a dropped goal is a scope change, `references/govern.md`), new tasks, and capacity entries for the month (`null` where unknown). Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py`.

6. **Draft the new documents**
   Draft `project-plan` and `team-checklist` (`references/draft.md`). Those types are not named by month, so an existing one follows draft.md step 2. Offer, do not create: `capacity-plan`, `weekly-plan`, `roadmap`, a charter review.

7. **Reply**
   What was carried over (counts by priority level), what was dropped, the decisions still needed, and the paths of the new drafts.

## Do not

- Move or close a milestone, or change a committed date, without the user.
- Finish, publish, send or commit.
