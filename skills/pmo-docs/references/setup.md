---
playbook_version: 1
---

Reads: pmo/config.yaml (if present).

# Setup

Set up a project's `pmo/` folder and starter registers.

## Steps

1. **Check for existing setup**
   Check if `pmo/config.yaml` exists. If it exists, do not overwrite anything.
   Compare its `schema_version` with the skill's current version (1):
   - Equal: project is current; nothing to do.
   - Older: a migration is due (none exist yet).
   - Newer: the skill is out of date; update the skill (`setup.py` exits 2).
   Stop after reporting the status.

2. **Gather configuration and confirm**
   Ask the user for initial project details (project name, project manager; priority order and week start use defaults unless mentioned). Unknown answers stay null and become open questions. Display the tree of files to be created and wait for one yes before running `setup.py` or writing any file (`SKILL.md`, Safety rule 3: ask before writing beyond the request):
   ```
   pmo/
   ├── bin/
   │   └── pmo
   ├── config.yaml
   ├── .gitignore         ignores .me
   ├── house-rules.md
   ├── documents/
   │   └── .gitkeep
   ├── views/             one rendered .md per register
   └── registers/
       ├── actions.yaml       ├── assumptions.yaml   ├── budget.yaml
       ├── capacity.yaml      ├── changes.yaml       ├── decisions.yaml
       ├── dependencies.yaml  ├── issues.yaml        ├── meetings.yaml
       ├── milestones.yaml    ├── objectives.yaml    ├── priorities.yaml
       ├── risks.yaml         ├── roster.yaml        ├── tasks.yaml
       └── teams.yaml
   ```
   Setup copies the project launcher `pmo/bin/pmo` (mode 755). On an existing project, `setup.py --launcher` writes only the launcher and replaces one that differs from the skill's: ask first when the project already has one (`SKILL.md`, Safety rule 3). Optional registers (`requirements`, `tests`, `environments`, `permissions`) are not created at setup; they are copied on their first entry (`references/track.md`).

3. **Run setup script**
   Execute `scripts/setup.py` with the chosen flags:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/setup.py [--name TEXT] [--manager TEXT] [--priority-order LIST] [--week-start DAY] [--launcher]`
   Pass `--week-start` when it is not Monday. Pass `--launcher` on an existing project to write or replace only `pmo/bin/pmo`.

4. **Verify and next steps**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check` to confirm registers and views are valid.
   Advise next steps:
   - Add your first tasks in `pmo/registers/tasks.yaml`.
   - Or draft the project charter.
   If the project has a git remote, note in one line that `pmo/` holds people's names.
