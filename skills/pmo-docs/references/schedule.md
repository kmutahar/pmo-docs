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
   `release-notes` cannot be scheduled: it needs a person present. `team-review` cannot be scheduled either: a person reads the result.
   A scheduled `month-start` run stops after listing the carry-over and changes no register.

2. **Record in config**
   Show the planned entry under `schedule:` in `pmo/config.yaml`:
   ```yaml
   schedule:
     - { recipe: <recipe>, when: "<when>" }
   ```
   Wait for the user's yes before writing (`SKILL.md`, Safety rule 3: a change to the config, a template or a playbook is always shown first).

3. **Print the cron line or scheduler call**
   Map `when` to standard 5-field cron syntax (`minute hour day-of-month month day-of-week`), using the machine's local time:
   - `Mon 08:00` -> `0 8 * * 1`
   - `1st 09:00` -> `0 9 1 * *`
   - `Fri 17:00` -> `0 17 * * 5`

   Print the cron command line for the user to add to their crontab (`crontab -e`):
   ```sh
   0 8 * * 1 cd /path/to/project && claude -p "run <recipe>; draft only, do not finish, publish or commit; for month-start stop after listing the carry-over" --allowedTools "Skill" "Read" "Write" "Edit" "Glob" "Grep"
   ```
   The prompt explicitly states the draft-only limit because an unattended cron run does not read this playbook (the `month-start` stop is in the prompt for the same reason).
   Replace /path/to/project with the absolute path of the project, and use the full path of `claude` if cron does not find it.
   Without --allowedTools the headless run is denied the tools it needs and writes nothing. Do not widen this list. `Write` and `Edit` here are not limited to `pmo/`: the unattended run can change any file in the project, and `paths.*` may point outside `pmo/`. Schedule it only in a project you trust.
   Never print permission-skipping flags (`--dangerously-skip-permissions`).

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

## List schedules ("what is scheduled?")

Read `schedule:` from `pmo/config.yaml` and print a table of `Recipe` and `When` (or say nothing is scheduled). Remind the user that `pmo/config.yaml` is the project's record and that they can run `crontab -l` (or check their agent harness) to confirm what is installed matches.

## Stop a schedule ("stop X")

Find the matching entry in `schedule:` in `pmo/config.yaml`, show the planned removal, and wait for a yes (`SKILL.md`, Safety rule 3). Remove the entry from `pmo/config.yaml`, then remind the user to delete the matching line from `crontab -e` (or cancel the job in their agent harness).

## Do not

- Install a cron entry or edit crontab.
- Write or install a git hook.
- Finish, publish, send or commit.
