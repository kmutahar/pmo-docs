# pmo-docs

A project office kept in plain files and run by your AI coding agent. A project keeps its facts in YAML **registers** (tasks, risks, issues, decisions, ...). Scripts render **views** from them, and the agent drafts **documents** (status reports, plans, charters, ...) from **templates** whose checks a script verifies.

> **Status: v0.2.0 released.** Registers, views, documents, checks, generators and recipes work today. Release history is in [`CHANGELOG.md`](CHANGELOG.md); the plan, decisions and later versions are in [`docs/PLAN.md`](docs/PLAN.md).

## How it works

- **Registers are the only source of facts.** Each entry is one line with its own id (for example `T-014`). The agent never invents facts.
- **Views** are summaries rendered from the registers and never edited by hand.
- **Documents** are drafted from a template, for one period (a week, a month) or once. A document is a draft until **Finish** records the template version, removes the template's comments, runs the checks and marks it finished.
- **Checks** are rules a draft must pass, so correctness does not depend on the model remembering them.
- A project can **override** a template or add **house rules**. House rules win over the skill's rules, except the safety rules below.

The words used here are defined in [`GLOSSARY.md`](GLOSSARY.md).

## What it adds to a project

```
pmo/
  config.yaml      only your settings; defaults come from the skill
  registers/       tasks, risks, issues, decisions, ...
  views/           generated summaries and catalogue (commit them)
  documents/       drafts and finished documents
  templates/       only the templates you changed or added
  playbooks/       only the playbooks you changed or added
  house-rules.md   your own rules
```

Setup asks a few questions (project name, project manager, priority order; the week start only if you mention weeks), shows the files it will write and waits for your yes. It never overwrites a file.

Supported doc types: project charter, project plan, roadmap, weekly plan, capacity plan, team checklist, weekly/monthly status report, stakeholder update, release notes, change request, meeting minutes, decision log, delivery report, retrospective, overdue report, and docs audit report.

## Install

Claude Code, as a plugin:

```
/plugin marketplace add kmutahar/pmo-docs
/plugin install pmo-docs@pmo-docs
```

The marketplace and the plugin are both named `pmo-docs` (see `.claude-plugin/` and `skills/pmo-docs/.claude-plugin/`). Installing copies only the skill folder.

The short form `kmutahar/pmo-docs` clones over SSH. If you have no SSH key on GitHub, add the marketplace with the web address instead:

```
/plugin marketplace add https://github.com/kmutahar/pmo-docs.git
```

Other agents: copy the folder `skills/pmo-docs/` into the agent's skills folder, or download `pmo-docs-<version>.zip` from the [GitHub release](https://github.com/kmutahar/pmo-docs/releases) and unzip it there. It works alone; nothing else in this repo is needed.

Claude Code is the only agent verified. Other agents are untested.

Needs Python 3.10 or newer on Linux or macOS (Windows: use WSL). Nothing to `pip install`: PyYAML is bundled with the skill.

## Quick start

From nothing to a first rendered view. Run the agent in your project's root folder.

1. Ask the agent: "set up a project office". It asks for the project name, project manager and priority order, shows the files it will create and waits for your yes. Then it runs the setup script.
2. Add your people and first tasks. Ask the agent ("add a task: set up staging, high priority, due 2026-03-10"), or edit `pmo/registers/roster.yaml` and `pmo/registers/tasks.yaml` yourself, one entry per line:
   ```yaml
   tasks:
     - {id: T-1, title: Set up staging server, priority: high, owner: sam, status: in-progress, due: 2026-03-10}
   ```
3. Render the views: ask the agent, or run `render_views.py` (below). It validates the registers first and writes `pmo/views/tasks.md` and one view per register.

Without an agent, the same steps are plain commands. Set `SKILL` to the skill folder (`skills/pmo-docs/` in a clone of this repo) and work in your project's root:

```sh
SKILL=/path/to/skills/pmo-docs
python3 "$SKILL/scripts/setup.py" --name "My project" --manager "Your Name"
# edit pmo/registers/tasks.yaml and pmo/registers/roster.yaml
python3 "$SKILL/scripts/render_views.py"
python3 "$SKILL/scripts/render_views.py" --check
```

`setup.py` never overwrites a file. `render_views.py` prints `registers valid; wrote 17 views to pmo/views`, or the errors it found (and exits 1). `--check` writes nothing and exits 1 when the registers are invalid or a view is stale. Every script answers `--help`.

Next, ask for a document ("draft the project charter", "weekly-status"). A worked example with a small example project is in [`docs/walkthrough.md`](docs/walkthrough.md).

## Commands

In Claude Code, two slash commands automate setup and publishing:
- `/pmo-docs:init`: interactive project office setup.
- `/pmo-docs:publish`: review and publish finished documents to a configured folder or documentation repository.

Skill-only installs can run the corresponding scripts (`setup.py` and `publish.py`) directly from the terminal.

## Generators

Four document types are generated by default (`generator: true` in the skill's defaults: `decision-log`, `team-checklist`, `project-plan`, `status-report`). They are pre-filled mechanically from registers using `scripts/generate.py`. The agent fills only what was left (prose placeholders, comments, open questions). To disable a generator for a doc type in your project, set `generator: null` under that doc type in your `pmo/config.yaml`.

## Publishing

Finished documents can be published to a publish target folder inside the project or to another local repository using `/pmo-docs:publish` (or `publish.py` directly).
- `mode: none` (default): nothing is published.
- `mode: folder`: copies finished documents into a folder inside your project.
- `mode: repo`: copies finished documents to another local repository. The command asks before committing in that repository and never pushes.

## Week start and catalogue

- **Week start**: Set `project.week_start` (e.g. `monday`, `sunday`, `saturday`) in `pmo/config.yaml` to configure the day working weeks begin. Weekly document windows and naming adjust automatically.
- **Catalogue**: `pmo/views/catalogue.md` is generated by `render_views.py`, listing every doc type, its title, made-by mode (`generator` or `agent`), when to produce it, and publish settings.

## Overrides and drift

A project can override templates in `pmo/templates/` and playbooks in `pmo/playbooks/`. Each override records `based_on: <name>@<version>`. When the skill's default template or playbook advances, `docs_audit.py` warns of drift.

## What it reads and writes

- It reads the project's `pmo/` folder, the skill's own files and, only as evidence, read-only git history. Drafting release notes with `--repo` also reads the git history of another local repository you name.
- It writes only inside the folders named in `pmo/config.yaml` (by default, under `pmo/`). Anything else is shown first and waits for your yes. The one exception you set up yourself: `/pmo-docs:publish` copies finished documents to `publish.path` and, in `repo` mode, commits there only after a second yes. It never pushes.
- It never overwrites a file you edited by hand.
- The rules are in [`skills/pmo-docs/SKILL.md`](skills/pmo-docs/SKILL.md) (Safety rules).

## Safety

- Its scripts send nothing over the network. Nothing is posted or published except through `/pmo-docs:publish`, which never pushes.
- It never runs `git add`, commit or push unless you ask. You commit when you choose; git is the backup. The commit model is in [`skills/pmo-docs/references/git.md`](skills/pmo-docs/references/git.md).
- `pmo/` holds people's names (the roster and the owners of entries). If your project's repo is public, so are they.
- In Claude Code, the scripts are allowed by the skill for the turn that loads it. Later turns may ask for your permission again; that is expected.

## Check the registers in your own git hook

The skill installs no hook. If you want one, call `render_views.py --check` from your own pre-commit hook: it writes nothing and exits 1 when the registers are invalid or a view is stale. The recipe and the reasons are in [`skills/pmo-docs/references/git.md`](skills/pmo-docs/references/git.md) (Checking registers in your own hook).

## Limits

- Built for one writer per project: one person, or one agent session, edits the registers at a time. Teams can use it: duplicate ids are caught and views render again cleanly after a merge. A command that fixes duplicate ids comes in 1.0; documents edited by several writers come after 1.0.
- English only until v0.3.

## Roadmap

| Version | Theme |
|---|---|
| v0.1 | Core skill: registers, views, templates and checks, setup, plugin manifest (released) |
| v0.2 | Generators, calendar, publishing with `init` and `publish` commands, playbook overrides and drift warnings, a catalogue of doc types (released) |
| v0.3 | Languages and translation, intake from chat exports |
| v0.4 | Stacks, technical and domain templates, and their registers |
| v0.5 | Other agents and unattended runs: a launcher, schedules, a shared hook |
| 1.0 | Stable formats, a command that fixes duplicate ids, a test that a v0.1 project still works |
| After 1.0 | Documents edited by several writers |

## Contributing

Run the tests with `python3 -m unittest discover tests`. CI runs them and a privacy scrub on every push and pull request. The local commit gate (`.githooks/`) also needs a list of names that only the maintainer has, so contributors leave it off and rely on CI. The rules for working on this repo, and the maintainer's procedures (evals, security scan, releases), are in [`AGENTS.md`](AGENTS.md).

## Licence

[MIT](LICENSE). Also: [privacy policy](PRIVACY.md) and [terms](TERMS.md).
