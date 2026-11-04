Reads: pmo/config.yaml (if present).

# Setup

Set up a project's `pmo/` workspace and starter registers.

## Steps

1. **Check for existing setup**
   Check if `pmo/config.yaml` exists. If it exists, do not overwrite anything.
   Compare its `schema_version` with the skill's current version (1):
   - Equal: project is current; nothing to do.
   - Older: a migration is due (none exist yet).
   - Newer: the skill is out of date; update the skill.
   Stop after reporting the status.

2. **Gather configuration**
   Ask the user for initial project details, showing defaults:
   - Project name (default: null)
   - Project manager (default: null)
   - Week start day (default: monday; choices: monday, sunday, saturday)
   - Priority order (default: high, medium, low)
   Unknown answers stay null and become open questions.

3. **Confirm layout**
   Display the tree of files to be created and wait for confirmation:
   ```
   pmo/
   ├── config.yaml
   ├── house-rules.md
   ├── documents/
   │   └── .gitkeep
   └── registers/
       ├── actions.yaml       ├── assumptions.yaml   ├── budget.yaml
       ├── capacity.yaml      ├── changes.yaml       ├── decisions.yaml
       ├── dependencies.yaml  ├── issues.yaml        ├── meetings.yaml
       ├── milestones.yaml    ├── objectives.yaml    ├── priorities.yaml
       ├── risks.yaml         ├── roster.yaml        ├── tasks.yaml
       └── teams.yaml
   ```
   Wait for the user to confirm before writing anything.

4. **Run setup script**
   Execute `scripts/setup.py` with the chosen flags:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/setup.py [--name TEXT] [--manager TEXT] [--week-start DAY] [--priority-order LIST]`

5. **Verify and next steps**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check` to confirm registers and views are valid.
   Advise next steps:
   - Add your first tasks in `pmo/registers/tasks.yaml`.
   - Or draft the project charter.
   If the project has a git remote, note in one line that `pmo/` holds people's names.
