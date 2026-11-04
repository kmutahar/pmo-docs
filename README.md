# pmo-docs

A project office kept in plain files and run by your AI coding agent. A project keeps its facts in YAML **registers** (tasks, risks, issues, decisions, ...). Scripts render **views** from them, and the agent drafts **documents** (status reports, plans, charters, ...) from **templates** whose checks a script verifies.

> **Status: under construction. Nothing is released yet.** This README describes what v0.1 will do. The build plan, decisions and checklist are in [`docs/PLAN.md`](docs/PLAN.md).

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
  views/           generated summaries (commit them)
  documents/       drafts and finished documents
  templates/       only the templates you changed or added
  house-rules.md   your own rules
```

Setup asks a few questions (project name, project manager, priority order), shows the files it will write and waits for your yes. It never overwrites a file.

## Install

Claude Code, as a plugin:

```
/plugin marketplace add kmutahar/pmo-docs
/plugin install pmo-docs@pmo-docs
```

The marketplace and the plugin are both named `pmo-docs` (see `.claude-plugin/`).

Other agents: copy the folder `skills/pmo-docs/` into the agent's skills folder. It works alone; nothing else in this repo is needed.

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

`setup.py` never overwrites a file. `render_views.py` prints `registers valid; wrote 16 views to pmo/views`, or the errors it found (and exits 1). `--check` writes nothing and exits 1 when the registers are invalid or a view is stale. Every script answers `--help`.

Next, ask for a document ("draft the project charter", "weekly-status"). A worked example with a finished project is in [`docs/walkthrough.md`](docs/walkthrough.md).

## What it reads and writes

- It reads the project's `pmo/` folder, the skill's own files and, only as evidence, read-only git history.
- It writes only inside the folders named in `pmo/config.yaml` (by default, under `pmo/`). Anything else is shown first and waits for your yes.
- It never overwrites a file you edited by hand.
- The rules are in [`skills/pmo-docs/SKILL.md`](skills/pmo-docs/SKILL.md) (Safety rules).

## Safety

- Its scripts send nothing over the network, and nothing is posted or published.
- It never runs `git add`, commit or push unless you ask. You commit when you choose; git is the backup. The commit model is in [`skills/pmo-docs/references/git.md`](skills/pmo-docs/references/git.md).
- `pmo/` holds people's names (the roster and the owners of entries). If your project's repo is public, so are they.
- In Claude Code, the scripts are allowed by the skill for the turn that loads it. Later turns may ask for your permission again; that is expected.

## Check the registers in your own git hook

The skill installs no hook. If you want one, call `render_views.py --check` from your own pre-commit hook: it writes nothing and exits 1 when the registers are invalid or a view is stale. The recipe and the reasons are in [`skills/pmo-docs/references/git.md`](skills/pmo-docs/references/git.md) (Checking registers in your own hook).

## Limits

- Built for one writer per project: one person, or one agent session, edits the registers at a time. Teams can use it: duplicate ids are caught and views render again cleanly after a merge. Full team support comes after 1.0.
- English only until v0.3.

## Roadmap

| Version | Theme |
|---|---|
| v0.1 | Core skill: registers, views, templates and checks, setup, plugin manifest |
| v0.2 | Generators, calendar, publishing, `init` and `publish` commands |
| v0.3 | Languages and translation, intake from chat exports |
| v0.4 | Stacks and technical templates |
| v0.5 | Tested on other agents |
| 1.0 | Stable config format, tested upgrades from every 0.x release |

## Contributing

Run the tests with `python3 -m unittest discover tests`. CI runs them and a privacy scrub on every push and pull request.

## Licence

[MIT](LICENSE)
