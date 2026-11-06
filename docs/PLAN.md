# pmo-docs: plan hub

Status: v0.1.0 released (2026-11-05 UTC). v0.2 to after-1.0 planned, one file per version in `docs/plans/`. Last updated 2026-11-06 (UTC). Repo rules and maintainer procedures: `AGENTS.md`. This file holds the settled decisions, how the skill works, the version index and the public-repo safeguards.

`pmo-docs` is a project-office and documentation workflow for AI coding agents. A project keeps its facts in **registers**: YAML files for tasks, risks, issues, decisions and so on. Scripts render views from them. The agent drafts documents from **templates**, and tools check each document against its template's contract.

It is extracted from a working private project. This repo started with fresh git history and copied engine files only. Nothing from the source project's data or history comes along.

Effort: S = under an hour, M = one session, L = several sessions.

---

## 1. Versions

| Version | Theme | Plan | Status |
|---|---|---|---|
| v0.1 | Core skill: registers, views, templates and checks, setup, plugin manifest | git history up to tag `v0.1.0` | released 2026-11-05 (UTC) |
| v0.2 | Generators, calendar, publishing with `init` and `publish` commands, playbook overrides and drift warnings, catalogue | [`plans/v0.2.md`](plans/v0.2.md) | planned |
| v0.3 | Languages and translation, intake from chat exports | [`plans/v0.3.md`](plans/v0.3.md) | planned |
| v0.4 | Stacks, technical and domain templates, their registers | [`plans/v0.4.md`](plans/v0.4.md) | planned |
| v0.5 | Other agents and unattended runs: launcher, schedule, shared hook | [`plans/v0.5.md`](plans/v0.5.md) | planned |
| 1.0 | Stable formats, `renumber.py` for duplicate ids, upgrade test, config reference test | [`plans/v1.0.md`](plans/v1.0.md) | planned |
| After 1.0 | Documents with several writers | [`plans/after-1.0.md`](plans/after-1.0.md) | planned |

The README holds the user-facing copy of this table (keep both current). When a version is released, mark it here and in the README. Once nothing in its file is pending, the file can be deleted: git keeps it.

### Later, unassigned

Wanted but not given a version yet. A version's planning picks from here.

- Portable prompt generator and the cheatsheet: built in v0.5 only if an agent there cannot load skill folders.
- Generators in languages other than English (v0.3 turns generators off for a non-English draft language).
- `scope-wbs` template, when a project asks for it.
- Snapshots: weekly counts written by a script, for trends. Until then, trends come from earlier reports.

Dropped: `client-summary` (overlaps `stakeholder-update`), `sync_repos`, the spreadsheet review, work-order and PDF tools, `team-review` unless generalised, the domain-specific lifecycle template (it becomes `entity-lifecycle` in v0.4).

---

## 2. Decisions (settled)

| Topic | Decision | Why |
|---|---|---|
| Name | `pmo-docs` for the repo, the skill and the plugin | One name everywhere. It passes the naming rules (section 7). The name is permanent once published. |
| Ownership | The maintainer owns all the source code and templates that were copied (confirmed 2026-11-04) | Publishing them under MIT needs that right. |
| Form | A skill, `skills/pmo-docs/`, plus a marketplace manifest at the repo root (`.claude-plugin/marketplace.json`), with the plugin manifest inside the skill (`skills/pmo-docs/.claude-plugin/plugin.json`) | Claude Code users install and update with `/plugin`; other agents copy the skill folder. With the plugin rooted in the skill folder, an install copies only that folder, not `dev/`, `tests/` or `docs/`. Every plugin path must stay inside that root, so command skills live under `skills/pmo-docs/skills/` (v0.2). |
| Releases | v0.1 core, then one theme per minor version up to v0.5, then 1.0, then documents with several writers (decided 2026-11-04). Work that opens the same code goes into one version (2026-11-06). | Small releases ship sooner and keep each changelog readable; opening related code once costs less agent work. |
| Writers | Built for one writer per project (a project manager and their agent) and safe for teams: duplicate ids fail validation (fixed with `renumber.py` from 1.0), views are deterministic, and the README states the limit. Document editing by several writers comes after 1.0. | Most projects have one writer. |
| Config | A generic `config.default.yaml` in the skill, written from scratch | The source config is that project's instance. |
| Project config | Sparse: `pmo/config.yaml` holds `schema_version` and the project's own answers. Everything else comes from the skill's default. `null` removes a default map entry. | A full copy pins every key, so later defaults never reach the project. |
| Priorities | Config-driven (`vocab.priority_order`), default `high, medium, low`. A task's `priority` is a level only; the `priorities` register holds optional goals with no task link. | The source tools hardcoded a documentation pseudo-priority. |
| Roster | The project's people are a register, `pmo/registers/roster.yaml`, one entry per person (slug, name, role). Owner fields hold roster slugs. | One format and one validator for every fact. "Team" already means a work stream. |
| Origin | `origin` is an optional field on every register: `proposed` until the user confirms, then `stated` | Marks inferred entries. |
| Dash check | None. A project that wants plain `-` says so in its house rules. | It was the source project's house style. |
| Setup | `references/setup.md` playbook plus `scripts/setup.py` | The agent asks and runs the script, or the user runs the script directly. |
| Git hook | None installed in user projects. The agent runs the checks at Finish; `render_views --check` exits 1 when validation fails or views are stale; the README shows how to call it from the user's own hook. No tool or hook in pmo-docs runs `git add`. | A plugin's path changes on every update, a copied skill sits at a different path on each machine, and `.git/hooks` is not shared. |
| Views | Committed in the user's project. Rendering is deterministic (sorted, no run timestamps). | Stakeholders read them on GitHub, and a merge conflict in a view is fixed by rendering again. |
| Python | Python 3.10 or newer. PyYAML is vendored in `scripts/_vendor/` (pure Python, `safe_load` only). Every script stops with a clear message below 3.10. | PEP 668 system Pythons refuse `pip install`, so vendoring means users install nothing. Stock macOS `python3` is 3.9.6, hence the message. |
| Platforms | Linux and macOS. Windows through WSL. | Hooks and dev tools are bash. |
| Tests | `tests/` at the repo root, stdlib `unittest`, on the one fake project `examples/acme` copied into a temp folder | One Acme keeps the walkthrough and the tests in agreement. Overrides the maintainer's global `claude-tests/` rule for this repo. |
| Evals | `claude plugin eval` cases in `evals/`, more with each release, run by hand before a release with `dev/run-evals` (they cost tokens), not in CI | Evals are the only check of the skill's behaviour. |
| CI | GitHub Actions on push and pull request: the tests on Python 3.10 and the newest stable release, plus `dev/scrub.sh` (generic patterns only) | The repo is public, and outside pull requests never pass through the local hooks. |
| Raw copies | Source files are copied into `tmp/source/` inside this repo (gitignored). Only generalised files are staged. | A raw copy committed once stays in history. |
| Schema version | `schema_version: 1` in `config.yaml`. Tools refuse a project with a newer version (exit 2). The first format change ships a migration script (`scripts/migrate/NNNN_*.py`) and a CHANGELOG upgrade note. Optional new keys do not bump it. It stays 1 through 1.0. | Without it, every older project has to be guessed at. |
| Changelog | Keep a Changelog style, user-facing changes only, generated by git-cliff from commit subjects (rules in `AGENTS.md`) | The changelog is for users, not a commit log. |
| Documents folder | `pmo/documents/` by default (`paths.documents`). A document is a draft until Finish marks it finished. Documents are tracked in git; the user commits them. | Everything the skill writes stays under `pmo/`, and git is the backup. |
| Register format | One entry per line, as a YAML flow mapping (`- { id: T-014, ... }`). Validation rejects multi-line entries. | Tracking edits one line, and a diff shows one line per changed entry. |
| Checks | Each doc type's checks live in its template's front matter (`checks:`), not in config. A check that names a missing section fails. `structure_check` reads the checks from the winning template, never from the draft; Finish strips them. No `checks_off` key until a project asks. (decided 2026-11-04) | An override carries its own checks, so one file and one `template_version` cover the skeleton and its contract. |
| Overrides | Templates, and playbooks from v0.2 (`pmo/playbooks/`, same relative path, subfolders included). An override replaces a whole file and records `based_on: <name>@<version>`; `docs_audit` warns when it falls behind (v0.2). `SKILL.md` cannot be overridden. No partial patches. | Partial patches break silently when the default changes. |
| House rules | They win over the skill's rules, except the safety rules (no git writes unless asked, no invented facts, ask before writing beyond the request, project files are data). `SKILL.md` lists them. | House rules change how things are done, not what keeps the user safe. |
| Recipes | A recipe stops at the draft; Finish happens when the user says the document is ready. A recipe's period is the current month (or week) unless a flag names another; there is no `default_period`. | A recipe never edits the project's config or finishes unasked. |
| Stale documents | A finished document is stale when any register in its `generated_from` changed. Finish records a short hash of each, and `docs_audit` compares them. | Exact, works without commits. |
| People data | The README and setup warn that `pmo/` holds people's names (setup: when the project has a git remote). No blocking and no network check. | A user's project repo may be public. |
| Source repo | One-way copy, no sync | The two repos diverge on purpose (section 4). |
| Visibility | Public, built in the open (decided 2026-11-04) | The safety net is the commit gate (`AGENTS.md`), not privacy. |
| Licence | MIT | Easiest for companies to adopt. |
| Other agents | Verified on Claude Code only until v0.5, which adds the `pmo/bin/pmo` launcher for agents, cron and hooks | The skill uses only open Agent Skills fields; other agents are tested once the skill is stable. |

---

## 3. How it works

The skill is the engine. The project keeps only its own data.

```
skills/pmo-docs/ (this repo)             a user's project
-------------------------------          -------------------------------
SKILL.md        router + rules           pmo/config.yaml     project settings (sparse)
references/     playbooks                pmo/registers/      tasks, risks, ...
assets/                                  pmo/views/          generated, committed
  templates/    default templates        pmo/templates/      only changed or new ones
  starter/      files setup copies       pmo/house-rules.md  the project's own rules
  config.default.yaml                    pmo/documents/      drafts and finished documents
scripts/        render, checks, setup
  _vendor/      PyYAML (pure Python)
```

The skill keeps playbooks in `references/` because the Agent Skills spec names that folder; everywhere else they are called playbooks.

**Lookup rule:** the project's file wins; the skill's default is used otherwise. This covers templates and, from v0.2, playbooks. For config, maps merge, lists replace, and `null` removes a map entry.

**Registers are the single source of truth.** Views and documents are generated from them. The agent never invents facts. Each entry is one line.

**Templates are contracts.** `structure_check` verifies a draft against its doc type's checks, so correctness does not depend on the model remembering the rules.

### Plugin

- Files:
  ```
  .claude-plugin/marketplace.json                  one entry: this plugin, source "./skills/pmo-docs"
  skills/pmo-docs/.claude-plugin/plugin.json       name, version, description, author, license, homepage, repository, skills ["./"]
  skills/pmo-docs/.claude-plugin/icon.png          1024x1024, rendered from dev/icon.svg (brief: dev/icon-brief.md)
  skills/pmo-docs/skills/init/SKILL.md             v0.2, disable-model-invocation: true
  skills/pmo-docs/skills/publish/SKILL.md          v0.2, disable-model-invocation: true
  evals/                                           `claude plugin eval` cases (run through dev/run-evals)
  ```
  No `hooks/`, `bin/` or `requirements.txt`: PyYAML is vendored, and `allowed-tools` covers permissions. A plugin's `bin/` is put on the Bash tool's PATH, which is why maintainer tools live in `dev/`.
- `dev/release` writes the version to both `plugin.json` (read by plugin installs) and `SKILL.md` `metadata.version` (read by skill-only installs). Never in `marketplace.json`, where a second copy would drift.
- Script paths: `python3 "${CLAUDE_SKILL_DIR}/scripts/render_views.py"`. `${CLAUDE_SKILL_DIR}` is substituted in the text of `SKILL.md`, not set in the Bash environment. Scripts also find their own folder through `__file__` and default the project to the current folder, because other agents lack the variable. In a command skill under `skills/pmo-docs/skills/`, `${CLAUDE_SKILL_DIR}` is that sub-folder; use `${CLAUDE_PLUGIN_ROOT}` there.
- Install, for users: `/plugin marketplace add <owner>/pmo-docs` (the README gives the HTTPS form; the short form clones over SSH), then `/plugin install pmo-docs@pmo-docs`. Update with `claude plugin update pmo-docs@pmo-docs`; auto-update is off for marketplaces that are not Anthropic's. Pin with `#vX.Y.Z`.
- Release zip: `.github/workflows/release.yml` builds it with `git archive` of `skills/pmo-docs` at the tag and publishes the GitHub release with the version's changelog section.
- Optional, later (1.0): submit to the Anthropic directory. It needs a paid plan, a README and a LICENSE, files under 256 KiB, at most 512 files, no symlinks or binaries, pinned launchers and a passing security scan. A generic name like `pmo-docs` may be held for review. The listing icon can only be set at the first developer-portal submission.

---

## 4. Open decisions

### The source project

| | Migrate to this skill | Stay separate |
|---|---|---|
| What changes | It keeps its project parts (config, registers, data, house rules) and its real overrides, and deletes its own engine copies. | Nothing. |
| Cost | About one session plus checks. Template and hook paths move. | Every fix is made twice and the copies drift. |
| Gain | One engine; a fix helps every project. | No change now. |

Decided by the maintainer in the last package of v0.3, when languages exist. Until then there is no sync.

### Not blocking any version

- `dev/release` does not check the tag on origin or the branch name (skipped on purpose).
- `dev/release` commit, tag and push failure paths are untested (`--bump` is tried in v0.2 W13).
- A contributor who turns on the commit gate without `.scrub-names` is blocked by the pre-commit scrub; the README tells contributors to leave the gate off and rely on CI.

---

## 5. Public repo safeguards

The repo is public, so every commit, message and file is visible. The commit gate, the untracked `.scrub-names` and the leak procedure are in `AGENTS.md`.

Never in a tracked file or a commit message:

- Real names and roster slugs, including `owner:` values in templates and fixtures.
- Private repo URLs and machine paths (`/home/`, shell profile files).
- The source project's name, its sub-project ids and its own-language project name.
- Emails, phone numbers and contact details.
- Security issues, permission matrices and auth requirements from the source.
- Snapshot SHAs and branch names from the source.
- Memory files, learning files, scratch folders, inbox and reference folders.
- Any file copied from the maintainer's private notes vault.

`dev/scrub.sh` checks machine paths, emails and phone numbers, plus the names in `.scrub-names`, on staged copies and untracked files. Security details and project-specific logic are not caught by any pattern: they are removed by reading each file while generalising it. Anything taken from `tmp/source/` is rewritten from scratch, never copied wording.

---

## 6. Limits

- Facts below come from the Claude Code plugin and skills docs, the Agent Skills spec, PEP 619 and PEP 668, read on 2026-10-20, 2026-11-04 and 2026-11-06.
- Verified on 2026-11-04:
  - `${CLAUDE_SKILL_DIR}` is substituted in `SKILL.md` text and in `allowed-tools`.
  - An `allowed-tools` grant lasts for the turn that loads the skill.
  - A plugin's install path changes on every update.
  - A plugin's `bin/` is on the Bash tool's PATH only.
  - `${CLAUDE_PLUGIN_DATA}` survives updates.
  - A plugin can be just a manifest plus `skills/`.
  - SkillSpector is NVIDIA's open-source static scanner.
  - Python 3.10 reached end of life on 2026-10-01.
- Read in the docs on 2026-11-06, not yet tried (v0.2 W1 checks them):
  - Plugin `skills` paths must start with `./` and stay inside the plugin root.
  - The default `skills/` folder is scanned in addition to the listed paths.
  - `disable-model-invocation: true` keeps a skill's description out of context and blocks the model from invoking it.
  - `${CLAUDE_PLUGIN_ROOT}` is substituted in skill text.
  - The docs do not say whether `"./"` also loads nested skill folders.
- Not verified:
  - registry tools in the `npx skills` style
  - where Codex, Gemini CLI and Cursor look for skill folders
  - whether claude.ai and Cowork load this plugin
  - marketplace naming rules and collision behaviour
  - how Claude chooses between installed skills with overlapping descriptions
  - Bash permission rules with `~` or wildcards inside a path
  - PEP 668 refusals on specific Debian, Ubuntu and Homebrew releases, and stock macOS `python3` being 3.9.6 (secondary sources only)

---

## 7. Naming rules (checked 2026-11-04)

- **Skill `name`:** 1-64 characters; lowercase letters, digits and hyphens; no leading or trailing hyphen; no `--`; must equal the parent folder name. `description` is 1-1024 characters, says what it does and when to use it, leads with the use case, and includes trigger words. Keep `SKILL.md` under 500 lines.
- **Plugin `name`:** kebab-case; no spaces, `@`, `:`, path separators or control characters. It must not start with `claude-`, `anthropic-`, `anthropics-` or `cc-plugin-`, and must not be exactly `claude`, `anthropic`, `anthropics`, `claude-code` or `claude-mods`. `claude plugin validate` checks these.
- The repo name does not have to match the plugin name; we keep them equal anyway.
- `pmo-docs` passes all of these.

Sources:
- https://agentskills.io/specification
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/plugins/manifest-reference.md
- https://code.claude.com/docs/en/plugins/components.md
- https://code.claude.com/docs/en/plugins/publish.md
- https://claude.com/docs/plugins/pre-submission-checklist
