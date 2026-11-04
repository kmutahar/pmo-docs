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

Setup asks a few questions (project name, project manager, week start, priority order), shows the files it will write and waits for your yes. It never overwrites a file.

## Safety

- It writes only inside `pmo/`. Its scripts send nothing over the network.
- It never runs `git add`, commit or push unless you ask. You commit when you choose; git is the backup.
- `pmo/` holds people's names. If your project's repo is public, so are they.

## Install (planned for v0.1)

Claude Code, as a plugin:

```
/plugin marketplace add kmutahar/pmo-docs
/plugin install pmo-docs@pmo-docs
```

Other agents: copy `skills/pmo-docs/` into the agent's skills folder. Only Claude Code is verified; other agents are untested.

Needs Python 3.10 or newer on Linux or macOS (Windows: use WSL). Nothing to `pip install`: PyYAML is bundled.

## Limits

- Built for one writer per project. Teams can use it: duplicate ids are caught and views re-render cleanly after a merge. Full team support comes after 1.0.
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
