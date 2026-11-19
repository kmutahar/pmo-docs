# pmo-docs

[![Release](https://img.shields.io/github/v/release/kmutahar/pmo-docs)](https://github.com/kmutahar/pmo-docs/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/kmutahar/pmo-docs/ci.yml?branch=main&label=ci)](https://github.com/kmutahar/pmo-docs/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/kmutahar/pmo-docs)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform: Linux, macOS](https://img.shields.io/badge/platform-linux%20%7C%20macOS-lightgrey)
![Agent Skill](https://img.shields.io/badge/agent%20skill-claude%20code%20%7C%20codex%20%7C%20agy-informational)

An Agent Skill that keeps a project's tasks, risks and decisions in plain YAML files and drafts project documents from them, so the agent does not invent facts. Release history is in [`CHANGELOG.md`](CHANGELOG.md).

## Overview

You keep registers (tasks, risks, issues, decisions and more) as one-line YAML entries in your project. Scripts validate them and render read-only views. When you ask your coding agent for a weekly status, a project plan or release notes, it drafts from those registers and a template, and a script checks the draft before you finish it.

Example requests:

| You say | What happens |
| --- | --- |
| `weekly-status` | Drafts a status report from current tasks, risks and milestones. |
| `add a task: set up staging, high priority, due 2026-03-10` | Logs the task and updates the views. |
| `draft release notes` | Turns recent tasks, changes and git history into a release-notes draft. |
| `translate the status report into Arabic` | Writes `<name>.ar.md` next to the original and checks that structure, ids and numbers match. |

Terms such as register, view, draft and Finish are defined in [`GLOSSARY.md`](GLOSSARY.md).

## How it works

| Part | What it is |
| --- | --- |
| Registers | Plain YAML files, the only source of facts. Each entry is one line with its own id (for example `T-14`). |
| Views | Read-only summaries rendered from registers by scripts. Never edit them by hand. |
| Templates | Required sections and rules per document type. |
| Documents | Drafted for one period (a week, a month) or once. They stay drafts until you ask to Finish them. |
| Checks | Scripts that verify a draft, so correctness does not depend on the model remembering rules. |
| House rules | Your own rules in `pmo/house-rules.md`. They win over the skill's rules, except the safety rules. |

### Document types

Project charter, project plan, roadmap, weekly plan, capacity plan, team checklist, weekly and monthly status report, stakeholder update, release notes, change request, meeting minutes, decision log, delivery report, retrospective, overdue report, docs audit report, functional requirements, test acceptance, defect-gap report, entity lifecycle, API reference, integration guide, architecture overview and user guide.

## What it adds to a project

```text
pmo/
|-- bin/pmo            # project launcher (commit it)
|-- config.yaml        # only your settings; defaults come from the skill
|-- registers/         # tasks, risks, issues, decisions, requirements, tests, ... (some created on first use)
|-- views/             # generated summaries and catalogue (commit them)
|-- documents/         # drafts and finished documents
|-- templates/         # only the templates you changed or added
|-- playbooks/         # only the playbooks you changed or added
`-- house-rules.md     # your own rules
```

Setup asks a few questions (project name, project manager, priority order, and the week start only if you mention weeks), shows the files it will write and waits for your yes. It never overwrites a file.

## Prerequisites

- Python 3.10 or newer on Linux or macOS (Windows through WSL).
- An agent that reads Agent Skills (see the table under Installation).

Nothing to `pip install`: PyYAML is bundled with the skill, and the skill works alone.

## Installation

### Claude Code

```text
/plugin marketplace add kmutahar/pmo-docs
/plugin install pmo-docs@pmo-docs
```

This installs a copy of the skill folder only. The short form clones over SSH. Without an SSH key on GitHub, use the web address:

```text
/plugin marketplace add https://github.com/kmutahar/pmo-docs.git
```

### Antigravity, Codex and other agents

These agents read skills from `~/.agents/skills`. Copy the skill folder there from the release tag:

```sh
mkdir -p ~/.agents/skills
tmp=$(mktemp -d)
curl -fsSL https://github.com/kmutahar/pmo-docs/archive/refs/tags/v0.9.0.tar.gz | tar -xz -C "$tmp" \
  && [ -f "$tmp/pmo-docs-0.9.0/skills/pmo-docs/SKILL.md" ] \
  && rm -rf ~/.agents/skills/pmo-docs \
  && cp -R "$tmp"/pmo-docs-0.9.0/skills/pmo-docs ~/.agents/skills/pmo-docs
rm -rf "$tmp"
ls ~/.agents/skills/pmo-docs/SKILL.md ~/.agents/skills/pmo-docs/scripts
```

Restart the agent or open a new session and ask it to list its skills. `pmo-docs` should appear. For one project only, copy the folder to `.agents/skills/pmo-docs` in that project. You can also download `pmo-docs-<version>.zip` from the [GitHub release](https://github.com/kmutahar/pmo-docs/releases) and unzip it into `~/.agents/skills/`.

| Agent | Status |
| --- | --- |
| Claude Code | verified |
| Antigravity (`agy`) | verified |
| Codex | tested; works from `~/.agents/skills` |
| Gemini CLI, Cursor, Copilot | untested |

### Let an agent install it

Paste this into any coding agent. It reads [`docs/INSTALL_FOR_AGENTS.md`](docs/INSTALL_FOR_AGENTS.md), looks for existing copies, shows its plan, asks before every write, then installs and verifies.

```text
Read the raw text of https://raw.githubusercontent.com/kmutahar/pmo-docs/v0.9.0/docs/INSTALL_FOR_AGENTS.md (curl it, do not work from a summary), then follow it exactly to install and verify the pmo-docs skill for the agent you are running in. Respond in the user's language.
```

### Update

Claude Code installs a copy, so pull in new versions yourself:

```sh
claude plugin marketplace update pmo-docs && claude plugin update pmo-docs@pmo-docs
```

For other agents, run the commands above with the newer tag, or give the agent the prompt again. It compares the installed copy and asks before replacing it. Restart the agent afterwards. An update never touches your project's `pmo/` folder. If the project launcher changed, the agent shows the difference and asks first.

## Quick start

Run the agent in your project's root folder.

1. Ask: "set up a project office". The agent asks its questions, shows the files it will create and waits for your yes.
2. Add people and first tasks. Ask the agent ("add a task: set up staging, high priority, due 2026-03-10"), or edit the files yourself, one entry per line. `owner` is a roster slug.

   ```yaml
   # pmo/registers/roster.yaml
   roster:
     - {slug: sam, name: Sam Example, role: Project manager}

   # pmo/registers/tasks.yaml
   tasks:
     - {id: T-1, title: Set up staging server, priority: high, owner: sam, status: in-progress, due: 2026-03-10}
   ```

3. Render the views. Ask the agent, or run `render_views.py`. It validates the registers first, then writes `pmo/views/tasks.md` and one view per register plus the catalogue.

Then ask for a document: "draft the project charter" or "weekly-status". A worked example on a small fake project is in [`docs/walkthrough.md`](docs/walkthrough.md).

### Without an agent

Set `SKILL` to the skill folder (`skills/pmo-docs/` in a clone of this repo) and work in your project's root:

```sh
SKILL=/path/to/skills/pmo-docs
python3 "$SKILL/scripts/setup.py" --name "My project" --manager "Your Name"
# edit pmo/registers/tasks.yaml and pmo/registers/roster.yaml
python3 "$SKILL/scripts/render_views.py"
python3 "$SKILL/scripts/render_views.py" --check
```

`--check` writes nothing and exits 1 when the registers are invalid or a view is stale. Every script answers `--help`.

## Usage

### Scripts

| Script | Purpose |
| --- | --- |
| `setup.py` | Create the `pmo/` folder after you confirm. |
| `render_views.py` | Validate registers and render the views and catalogue. |
| `generate.py` | Pre-fill generated document types from registers. |
| `where.py` | Print where a document, its template and its inputs live. |
| `overdue.py` | Print overdue tasks, actions, milestones, open issues and open risks. |
| `renumber.py` | Fix duplicate ids after a merge. |
| `publish.py` | Copy finished documents to the publish target. |
| `parity_check.py` | Check that a translation matches its original. |
| `structure_check.py` | Check that documents keep the structure of their template. |
| `docs_audit.py` | Mechanical audit: stale, old and drifted documents, broken links, translations behind. |

### Slash commands (Claude Code)

| Command | What it does |
| --- | --- |
| `/pmo-docs:init` | Interactive project office setup. |
| `/pmo-docs:publish` | Review and publish finished documents to a configured folder or documentation repository. |

Skill-only installs run `setup.py` and `publish.py` from the terminal, or ask the agent. It shows the publish dry run and copies only after you say yes.

### Project launcher

Setup writes `pmo/bin/pmo` (mode 755; commit it). It finds the installed skill and runs any script with the project root set:

```sh
pmo/bin/pmo render_views --check
pmo/bin/pmo where status-report
pmo/bin/pmo overdue
```

It looks for the skill in `$PMO_DOCS_SKILL`, project skill folders, the Claude plugin cache and user skill folders (`~/.agents/skills`, `~/.claude/skills`, and so on). Cron jobs and teammates without Claude can use it without configuring skill paths.

## Configuration

`pmo/config.yaml` holds only your settings. Defaults come from the skill.

| Setting | What it controls |
| --- | --- |
| `project.week_start` | The day working weeks begin (`monday`, `sunday`, `saturday`). Weekly windows and file names follow it. |
| `languages` | Draft and translation languages. |
| `publish` | Where finished documents go (`mode: none`, `folder` or `repo`). |
| `schedule` | Recipes to run on a schedule. |
| `doc_types.<type>.generator` | Set to `null` to turn off the generator for that type. |

`pmo/views/catalogue.md` is rendered by `render_views.py`. It lists every document type with its title, who makes it (`generator` or `agent`), when to produce it and its publish settings.

### Generators

Four document types are pre-filled mechanically from registers by `scripts/generate.py`: `decision-log`, `team-checklist`, `project-plan` and `status-report`. The agent fills only what is left: prose placeholders, comments and open questions. Weekly reports count the month that holds at least four of the week's seven days.

### Languages and translation

Set `languages` once to draft or translate in another language (`ar` is Arabic; any language code works):

```yaml
languages:
  draft: en
  translations: [ar]
  ar: { label: AR, dir: rtl, glossary: pmo/data/glossary-ar.md }
```

The agent writes a translation only when you ask, and checks that headings, tables, ids, numbers, list items and ticked boxes match. The approved glossary is read-only: new terms go to a proposed file next to it. Generators write English only. Per-type settings and check scripts are in [`skills/pmo-docs/references/translate.md`](skills/pmo-docs/references/translate.md).

### Publishing

| `publish.mode` | Effect |
| --- | --- |
| `none` (default) | Nothing is published. |
| `folder` | Copies finished documents into a folder inside your project. |
| `repo` | Copies finished documents to another local repository. It asks before committing there and never pushes. |

### Scheduled runs

Ask the agent to "schedule the weekly status". It asks which recipe and when, shows the `schedule:` entry for `pmo/config.yaml` and waits for your yes. It then prints the cron line (or the agent's own scheduler call) for you to install. The skill never edits your crontab or installs a hook.

```yaml
schedule:
  - { recipe: weekly-status, when: "Mon 08:00" }
```

A scheduled run only drafts. It never finishes, publishes or commits. To refresh views without drafting, schedule `pmo/bin/pmo render_views`. The recipe is in [`skills/pmo-docs/references/schedule.md`](skills/pmo-docs/references/schedule.md).

### Overrides and drift

Override a template in `pmo/templates/` or a playbook in `pmo/playbooks/`. Each override records `based_on: <name>@<version>`. When the skill's default advances, `docs_audit.py` warns of drift.

## Intake from chat exports

Ask the agent to take tasks, finished work or decisions from a chat export. It reads the export itself, shows the proposed entries and writes nothing until you confirm. It does not copy the export into the project, and it refuses credentials: registers reject them.

## Technical documents and stacks

For documents drafted from code (API reference, integration guide, architecture overview, user guide, entity lifecycle), the agent reads your routes, data models, permissions and configuration using a stack reference file.

| Stack | Name |
| --- | --- |
| Next.js | `nextjs` |
| Express | `express` |
| ASP.NET Core | `aspnet-core` |
| Spring Boot | `spring-boot` |
| FastAPI (also covers Flask) | `fastapi` |
| Django | `django` |
| Flutter | `flutter` |

To use another stack, write `pmo/playbooks/stacks/<stack>.md` with the standard six headings and `playbook_version: 1`. See [`skills/pmo-docs/references/extend.md`](skills/pmo-docs/references/extend.md).

The agent reads your code and does not run it. Commands such as listing the API live are run by you, or by the agent only after you say yes.

## Working with git

**Hooks.** The skill installs none. To check registers on commit, call `pmo/bin/pmo render_views --check` from your own pre-commit hook. It writes nothing, stages nothing and exits 1 when the registers are invalid or a view is stale. Details are in [`skills/pmo-docs/references/git.md`](skills/pmo-docs/references/git.md).

**CI.** A GitHub Actions workflow can run the same check:

```yaml
name: pmo check
on:
  push: { paths: ["pmo/**"] }
  pull_request: { paths: ["pmo/**"] }
permissions: { contents: read }
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: curl -fsSL https://github.com/kmutahar/pmo-docs/archive/refs/tags/v0.9.0.tar.gz | tar -xz
      - run: pmo/bin/pmo render_views --check
        env: { PMO_DOCS_SKILL: pmo-docs-0.9.0/skills/pmo-docs }
```

**Two writers.** Two or more people can work on one project without a server or locks. One entry per line keeps diffs small. After a merge conflict in a register, keep both sides' new entries, resolve duplicates with `renumber.py` and render the views again. Merge rules for registers, views, drafts and finished documents are in [`git.md`](skills/pmo-docs/references/git.md) (Several writers). An editor on a draft is a warning, not a lock.

## Safety

**Reads:**
- Your `pmo/` folder (registers, views, config, documents and the untracked `pmo/.me` file) and the skill's own files.
- Documents, chat exports or pasted messages you point it at. Exports are read once and never copied into the project.
- Read-only git history of your project, and of another local repository you name for release notes with `--repo`.
- Your source, config and test files when drafting technical documents. It records setting and variable names, never values, never opens secret files such as `.env`, and never edits the code.
- Public framework documentation on the web, only when you ask for a new stack file. Nothing from your project is sent.
- The launcher reads `PMO_DOCS_SKILL`, `HOME` and `CLAUDE_CONFIG_DIR` and looks in the standard skill folders.

**Writes:**
- Inside your project: under `pmo/` (or the folders set in `pmo/config.yaml`) and the fixed files `pmo/config.yaml`, `pmo/.me`, `pmo/.gitignore` and `pmo/bin/pmo`. Anything else, an entry you did not state, an overwrite of a file you edited by hand, or any change to config, templates or playbooks is shown first and waits for your yes.
- Publishing copies finished documents to `publish.path` only after you run `/pmo-docs:publish` or say yes to the dry run. In `repo` mode this is the one place it writes outside your project, and committing there waits for a second yes.

**Never:**
- Makes network calls from its scripts. Your agent sends context to its model provider; the skill sends nothing on its own.
- Changes your git repository (staging, commits, pushes, resets, checkouts) or its hooks unless you ask. `publish` never pushes.
- Opens other folders or projects on your machine unless you ask.
- Follows instructions found in files, chat exports, code or web pages. It shows them to you and waits.
- Overwrites a hand-edited file without asking.
- Reads, asks for or stores credentials, passwords, tokens or keys, or copies a chat export, a pasted message, or the phone numbers and emails in it, into the project.

`pmo/` holds people's names (the roster and entry owners). If your project's repository is public, so are they. In Claude Code, the skill's allowed scripts and read-only git commands run without prompting during the turn that loads the skill, and later turns may prompt again. Full details are in [`PRIVACY.md`](PRIVACY.md) and [`skills/pmo-docs/SKILL.md`](skills/pmo-docs/SKILL.md) (Safety rules).

## Repository structure

```text
pmo-docs/
|-- skills/pmo-docs/   # the only part that ships: SKILL.md, scripts/, references/, assets/, skills/
|-- examples/acme/     # the one fake project used by tests, evals and the walkthrough
|-- docs/              # walkthrough and agent install guide
|-- tests/             # unit tests
|-- evals/             # eval cases
|-- dev/               # maintainer tools (scrub, release, icon)
|-- GLOSSARY.md
|-- AGENTS.md          # rules for working on this repo
|-- PRIVACY.md
`-- TERMS.md
```

## Limits and stability

- Generators write English only. The agent drafts other languages, and parity checks compare structure, ids and numbers, not wording.
- From `1.0`, the config format (`pmo/config.yaml`, `schema_version: 1`) and the register formats (`pmo/registers/*.yaml`) are stable. A project made with `1.x` keeps working with every later `1.x`: new keys and fields are optional, and a change that would invalidate an existing project waits for the next major version.
- Until `1.0` the formats can change. When one does, the release ships a migration script and an upgrade note in [`CHANGELOG.md`](CHANGELOG.md).

## Contributing

Run the tests with `python3 -m unittest discover tests`. CI runs them and a privacy scrub on every push and pull request. The local commit gate (`.githooks/`) needs a list of names that only the maintainer has, so contributors leave it off and rely on CI. Rules for working on this repo and the maintainer's procedures (evals, security scan, releases) are in [`AGENTS.md`](AGENTS.md) and [`dev/maintaining.md`](dev/maintaining.md).

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for the full text. Also: [privacy policy](PRIVACY.md) and [terms](TERMS.md).
