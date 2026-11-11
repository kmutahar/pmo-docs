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
  bin/             pmo project launcher (commit it)
  config.yaml      only your settings; defaults come from the skill
  registers/       tasks, risks, issues, decisions, requirements, tests, environments, permissions, ...
  views/           generated summaries and catalogue (commit them)
  documents/       drafts and finished documents
  templates/       only the templates you changed or added
  playbooks/       only the playbooks you changed or added
  house-rules.md   your own rules
```

Setup asks a few questions (project name, project manager, priority order; the week start only if you mention weeks), shows the files it will write and waits for your yes. It never overwrites a file.

Supported doc types: project charter, project plan, roadmap, weekly plan, capacity plan, team checklist, weekly/monthly status report, stakeholder update, release notes, change request, meeting minutes, decision log, delivery report, retrospective, overdue report, docs audit report, functional requirements, test acceptance, defect-gap report, entity lifecycle, API reference, integration guide, architecture overview, and user guide.

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

`setup.py` never overwrites a file. `render_views.py` prints `registers valid; wrote 21 views to pmo/views`, or the errors it found (and exits 1). `--check` writes nothing and exits 1 when the registers are invalid or a view is stale. Every script answers `--help`.

Next, ask for a document ("draft the project charter", "weekly-status"). A worked example with a small example project is in [`docs/walkthrough.md`](docs/walkthrough.md).

## Commands

In Claude Code, two slash commands automate setup and publishing:
- `/pmo-docs:init`: interactive project office setup.
- `/pmo-docs:publish`: review and publish finished documents to a configured folder or documentation repository.

Skill-only installs can run the corresponding scripts (`setup.py` and `publish.py`) directly from the terminal.

## Running outside a session

Setup writes a project launcher script into `pmo/bin/pmo` (mode 755; commit it to git). It finds the installed skill automatically and runs any script with the project root set:

```sh
pmo/bin/pmo render_views --check
pmo/bin/pmo where status-report
pmo/bin/pmo overdue
```

It looks for the skill in `$PMO_DOCS_SKILL`, project skill folders, the Claude plugin cache, and user skill folders (`~/.agents/skills`, `~/.claude/skills`, etc.). Unattended jobs (such as cron) or teammates without Claude can run scripts through `pmo/bin/pmo` without configuring skill paths.

## Generators

Four document types are generated by default (`generator: true` in the skill's defaults: `decision-log`, `team-checklist`, `project-plan`, `status-report`). They are pre-filled mechanically from registers using `scripts/generate.py`. The agent fills only what was left (prose placeholders, comments, open questions). To disable a generator for a doc type in your project, set `generator: null` under that doc type in your `pmo/config.yaml`.

## Languages and translation

Set `languages` in `pmo/config.yaml` to write documents in a language other than English or to translate them:

```yaml
languages:
  draft: en
  translations: [xx]
  xx: { label: XX, dir: rtl, glossary: pmo/data/glossary-xx.md }
```

A translation is a file next to its original, `<name>.xx.md`, made with the `translate` playbook and never unasked. `doc_types.<type>.translate` (`in-period` or `after-close`) says when; `doc_types.<type>.translations` limits the languages for one type. `parity_check.py` compares a translation with its original (headings, tables, ids, numbers) and `docs_audit.py` reports a translation behind its original. The approved glossary is read only; new terms go to a proposed file next to it. Generators write English only.

## Intake from chat exports

Ask the agent to take tasks, finished work or decisions from a chat export. It reads the export itself, shows the proposed entries and writes nothing until you confirm. It does not copy the export into the project, and it refuses credentials: registers reject them.

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

## Technical documents and stacks

For documents drafted from code (API reference, integration guide, architecture overview, user guide, entity lifecycle), the agent reads your repository's code, routes, data models, permissions and configuration using stack reference files.

Seven stacks ship with the skill: Next.js (`nextjs`), Express (`express`), ASP.NET Core (`aspnet-core`), Spring Boot (`spring-boot`), FastAPI (`fastapi`, also covers Flask), Django (`django`), and Flutter (`flutter`).

- **Add a stack**: To use a stack that is not shipped, write `pmo/playbooks/stacks/<stack>.md` with the standard six headings and `playbook_version: 1` (`skills/pmo-docs/references/extend.md`).
- **Safety**: The agent reads your code and does not run it. Commands like listing the API live are run by you, or by the agent only after you say yes (`skills/pmo-docs/SKILL.md`, Documents).

## What it reads and writes

- It reads the project's `pmo/` folder, the skill's own files and, only as evidence, read-only git history. Drafting release notes with `--repo` also reads the git history of another local repository you name. Drafting a technical document reads your project's source code (routes, models, config and test files, names only) and runs read-only git on it.
- It writes only inside the folders named in `pmo/config.yaml` (by default, under `pmo/`). Anything else is shown first and waits for your yes. The one exception you set up yourself: `/pmo-docs:publish` copies finished documents to `publish.path` and, in `repo` mode, commits there only after a second yes. It never pushes.
- It never overwrites a file you edited by hand.
- The rules are in [`skills/pmo-docs/SKILL.md`](skills/pmo-docs/SKILL.md) (Safety rules).

## Safety

- Its scripts send nothing over the network. Nothing is posted or published except through `/pmo-docs:publish`, which never pushes.
- It never runs `git add`, commit or push unless you ask. You commit when you choose; git is the backup. The commit model is in [`skills/pmo-docs/references/git.md`](skills/pmo-docs/references/git.md).
- `pmo/` holds people's names (the roster and the owners of entries). If your project's repo is public, so are they.
- In Claude Code, the scripts are allowed by the skill for the turn that loads it. Later turns may ask for your permission again; that is expected.

## Check the registers in your own git hook

The skill installs no hook. If you want one, call `pmo/bin/pmo render_views --check` from your own pre-commit hook: it writes nothing, stages nothing, and exits 1 when the registers are invalid or a view is stale. The recipe and the reasons are in [`skills/pmo-docs/references/git.md`](skills/pmo-docs/references/git.md) (Checking registers in your own hook).

## Limits

- Built for one writer per project: one person, or one agent session, edits the registers at a time. Teams can use it: duplicate ids are caught and views render again cleanly after a merge. A command that fixes duplicate ids comes in 1.0; documents edited by several writers come after 1.0.
- Generators write English only; other languages are drafted by the agent. Parity checks compare structure, ids and numbers, not wording.

## Roadmap

| Version | Theme |
|---|---|
| v0.1 | Core skill: registers, views, templates and checks, setup, plugin manifest (released) |
| v0.2 | Generators, calendar, publishing with `init` and `publish` commands, playbook overrides and drift warnings, a catalogue of doc types (released) |
| v0.3 | Languages and translation, intake from chat exports (released) |
| v0.4 | Stacks, technical and domain templates, and their registers (released) |
| v0.5 | Other agents and unattended runs: a launcher, schedules, a shared hook |
| 1.0 | Stable formats, a command that fixes duplicate ids, a test that a v0.1 project still works |
| 1.0.1 | Verification release: the evals, the security scan and the install check |
| After 1.0 | Documents edited by several writers |

## Contributing

Run the tests with `python3 -m unittest discover tests`. CI runs them and a privacy scrub on every push and pull request. The local commit gate (`.githooks/`) also needs a list of names that only the maintainer has, so contributors leave it off and rely on CI. The rules for working on this repo, and the maintainer's procedures (evals, security scan, releases), are in [`AGENTS.md`](AGENTS.md).

## Licence

[MIT](LICENSE). Also: [privacy policy](PRIVACY.md) and [terms](TERMS.md).
