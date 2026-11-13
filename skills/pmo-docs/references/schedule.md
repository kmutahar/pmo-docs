---
playbook_version: 1
---

Reads: pmo/config.yaml (schedule, paths.playbooks), pmo/house-rules.md.

# Schedule

Record scheduled recipe runs in `pmo/config.yaml` and print the exact commands for the user to install on their system or schedule in their agent harness.

A scheduled run drafts only: it must never Finish, publish, or commit. The skill installs nothing itself.

## Steps

1. **Ask which recipe and when**
   Ask which recipe to schedule and when it should run (for example `weekly-status` at `Mon 08:00`).
   Known recipes: `weekly-status`, `monthly-status`, `month-start`, `overdue-report`, `docs-audit`, plus any custom playbook under `paths.playbooks` (`pmo/playbooks/<name>.md`).
   `release-notes` cannot be scheduled: it needs a person present.
   A scheduled `month-start` run stops after listing the carry-over and changes no register.

2. **Record in config**
   Show the planned entry under `schedule:` in `pmo/config.yaml`:
   ```yaml
   schedule:
     - { recipe: <recipe>, when: "<when>" }
   ```
   Wait for the user's yes before writing (`SKILL.md`, Ask before writing beyond the request).

3. **Print the cron line or scheduler call**
   Map `when` to standard 5-field cron syntax (`minute hour day-of-month month day-of-week`), using the machine's local time:
   - `Mon 08:00` -> `0 8 * * 1`
   - `1st 09:00` -> `0 9 1 * *`
   - `Fri 17:00` -> `0 17 * * 5`

   Print the cron command line for the user to add to their crontab (`crontab -e`):
   ```sh
   0 8 * * 1 cd /path/to/project && claude -p "run <recipe>; draft only, do not finish, publish or commit"
   ```
   The prompt explicitly states the draft-only limit because an unattended cron run does not read this playbook.
   Never print permission-skipping flags.

   If the agent harness provides its own session-scheduling tool, show the equivalent call with the same prompt and timing.

4. **Scheduled view refresh and git hook**
   To refresh views on a schedule without drafting documents, show the optional cron line:
   ```sh
   pmo/bin/pmo render_views
   ```
   To check that views are current before each commit, show the optional pre-commit hook line for the user's own hook or hook manager:
   ```sh
   pmo/bin/pmo render_views --check
   ```

5. **Repository sync**
   To pull changes from a remote repository before running a scheduled recipe, add a `git pull` command before the agent command (the skill never pulls).

## Do not

- Install a cron entry or edit crontab.
- Write or install a git hook.
- Finish, publish, send or commit.
