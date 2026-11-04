# pmo-docs: build and release plan

Status: plan only. Nothing is built yet. Last updated 2026-11-04 (second review).

`pmo-docs` is a project-office and documentation workflow for AI coding agents. A project keeps its facts in **registers** (YAML files: tasks, risks, issues, decisions, and so on). Scripts render views from them, and the agent drafts documents from **templates** that tools check against a contract.

It is extracted from a working private project. This repo starts with fresh git history and copies engine files only. Nothing from the source project's data or history comes along.

Effort: S = under an hour, M = one session, L = several sessions.

---

## 1. Decisions (settled)

| Topic | Decision | Why |
|---|---|---|
| Name | `pmo-docs` for the repo, the skill and the plugin | One name everywhere. It passes the naming rules (section 9). The name is permanent once published. |
| Ownership | The maintainer owns all the source code and templates being copied (confirmed 2026-11-04) | Publishing them under MIT needs that right. |
| Form for v0.1 | A skill, `skills/pmo-docs/`, plus a plugin manifest at the repo root (`.claude-plugin/plugin.json` and `marketplace.json`) | Claude Code users install and update with `/plugin`; other agents copy the skill folder. The manifest is two small files and needs no hooks, `bin/` or venv. |
| Layout | `skills/pmo-docs/` from day one | The manifest sits at the repo root, so the skill folder never moves. |
| Releases | v0.1 core, then one M-sized theme per minor version up to v0.5, then 1.0, then team support (decided 2026-11-04) | See section 5. Small releases ship sooner and keep each changelog readable. |
| Writers | Built for one writer per project (a project manager and their agent) and safe for teams: duplicate ids fail validation, views are deterministic, and the README states the limit. Full team support comes after 1.0. | Most projects have one writer. A team must not be broken, but ids that cannot collide and a shared hook can wait. |
| v0.1 languages | English only | No RTL, digit or connector-word logic to generalise yet. Translations arrive in v0.3. |
| v0.1 tools | Core only: `pmo_common`, `render_views`, `structure_check`, `docs_audit`, `overdue`, `where`, `setup` | Little project coupling. Generators and extras wait until they are de-hardcoded. |
| v0.1 content | Only the templates and registers that a v0.1 playbook or recipe uses and a test covers. Phase B picks them from the source (27 templates, 19 registers). | Each one shipped is a public contract under `schema_version` that needs checks, fixture data and tests, and no real project uses v0.1 before v0.3. The rest arrive with the release that needs them. |
| Technical templates | Not in v0.1 (lifecycle, API reference, user guide, and similar) | They need per-stack rules (v0.4). |
| Config | A new generic `config.default.yaml` in the skill, **not a copy** of the source project's | The source config is that project's instance. |
| Project config | Sparse: `pmo/config.yaml` holds `schema_version` and the project's own answers. Everything else comes from the skill's default. `null` removes a default map entry (for example a doc type the project does not use). | A full copy pins every key, so later defaults never reach the project. |
| Priorities | Config-driven (`vocab.priority_order`), default P1-P3, no special "DOC" level | The source tools hardcode a documentation pseudo-priority. |
| Setup | `setup.md` playbook **plus** `scripts/setup.py` | The agent asks for the project name and project manager and runs the script, or the user runs the script directly. |
| Git hook | None installed in user projects. The agent runs the checks at Finish; `render_views --check` exits 1 when validation fails or views are stale; the README shows how to call it from the user's own hook. No tool or hook in pmo-docs runs `git add`. | A hook must call the scripts by absolute path, but a plugin's path changes on every update, a copied skill sits at a different path on each machine, and `.git/hooks` is not shared with teammates. The source hook also staged views without being asked. |
| Views | Committed in the user's project. Rendering is deterministic (sorted, no run timestamps). | Stakeholders read them on GitHub, and a merge conflict in a view is fixed by rendering again. |
| Python | Python 3.10 or newer. PyYAML is vendored in `scripts/_vendor/` (pure Python, `safe_load` only). Every script stops with a clear message below 3.10. | `pip install pyyaml` is refused by PEP 668 system Pythons (current Debian and Ubuntu, Homebrew), so vendoring means users install nothing. 3.10 is past end of life (2026-10-01) but is still Ubuntu 22.04's Python. Stock macOS `python3` is 3.9.6, hence the clear message. |
| Platforms | Linux and macOS. Windows through WSL. | Hooks and dev tools are bash, and Windows has no `python3` by default. |
| Tests | `tests/` at the repo root, run with stdlib `unittest` (`python3 -m unittest discover tests`) on the one fake project, `examples/acme`, copied into a temp folder | Conventional layout. One Acme keeps the walkthrough and the tests in agreement. `unittest` keeps the no-new-dependency rule. This overrides the maintainer's global `claude-tests/` rule for this repo only. |
| Evals | Two `claude plugin eval` cases from v0.1, more with each release. Run by hand before a release (they cost model tokens), not in CI. | Unit tests cover the scripts only. With Acme as the only user, evals are the only check of the skill's behaviour. |
| CI | GitHub Actions on push and pull request **from the first commit**: the tests on Python 3.10 and the newest stable release, plus `dev/scrub.sh` (the generic patterns only; `.scrub-names` never leaves the maintainer's machine) | The repo is public already, and outside pull requests never pass through the local hooks. |
| Raw copies | Source files are copied into `tmp/source/` **inside this repo** (gitignored). Only generalised files are ever staged. | The repo is public: a raw copy committed once stays in history even after it is generalised. The name scrub cannot catch project-specific logic or security details. |
| Schema version | `schema_version: 1` in `config.yaml` from v0.1. Tools refuse a project with a newer version than they know. Migration scripts (`scripts/migrate/NNNN_*.py`) are written only when the first format change happens. | Without it, every project made before the field exists has to be guessed at. |
| Changelog | Keep a Changelog style: user-facing changes only. `chore`, `ci`, `test`, `style`, `build`, `refactor` and `docs(plan\|dev\|memory)` commits are left out; breaking changes and non-conventional commits are always kept. Breaking changes use `feat!:` or `fix!:` (subjects have no body); bumping `schema_version` or renaming a config key or a template section is breaking. `CHANGELOG.md` is first committed by the v0.1.0 release. | The changelog is for users, not a commit log. A committed `[Unreleased]` section would go stale at every commit. |
| Vocabulary | One term per concept, defined in `GLOSSARY.md` | See the glossary for the canonical words and the ones to avoid. |
| Documents folder | `pmo/documents/` by default; a project can change it in config (`paths.documents`). A document is a draft until Finish marks it finished. Documents are tracked in git, never gitignored; the user commits them when they choose. | Everything the skill writes stays under `pmo/`, the user's repo root stays clean, and git is the backup (3.1, fix 2). v0.1 has no publish step, so finished documents stay where they were drafted. |
| Register format | One entry per line, as a YAML flow mapping (`- { id: T-014, ... }`). Validation rejects multi-line entries. | Tracking edits one line (3.1, fix 13), and a diff shows one line per changed entry. The source already uses this form. |
| Overrides | Template overrides only in v0.1; projects change behaviour through house rules. An override records `based_on: <type>@<version>` from v0.1; the drift warning comes in v0.2. | A whole-file playbook override never receives fixes again. A `based_on` missing from early overrides could never be filled in later. |
| House rules | They win over the skill's rules, except the safety rules: no `git add`, commit or push unless asked; no invented facts; nothing written without consent. `SKILL.md` lists the safety rules. | House rules let a project change how things are done, not what keeps the user safe. |
| Stale documents | A finished document is stale when any register it was made from has changed. Finish records a short hash of each `generated_from` register, and `docs_audit` compares them. | Exact, works without commits, and lets the user commit whenever they like. |
| People data | The README and setup warn that `pmo/` holds people's names (setup: when the project has a git remote). No blocking and no network check. | A user's project repo may be public. |
| Source repo | One-way copy, no sync | The two repos diverge on purpose. Whether the source project migrates to this skill is decided in section 6. |
| Visibility | **Public, built in the open** (decided 2026-11-04) | The maintainer is happy to code in public. The safety net is the commit gate, not privacy: `.githooks/pre-commit` runs `dev/scrub.sh` and `.githooks/commit-msg` checks messages, both against the untracked `.scrub-names`. A leak committed while private would still show in the history once public, so the gate matters either way. |
| Licence | MIT | Easiest for companies to adopt. GPL-3.0 would only matter if forks had to stay open. AGPL adds almost nothing for a local tool and many companies ban it. |
| Other agents | Verified on Claude Code only | The skill uses only open Agent Skills fields. The README says other agents are untested. They are tested once the skill is stable. |
| Commits | Never commit or push without the maintainer's approval | Standing rule. |

---

## 2. How it works

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

**Lookup rule:** the project's file wins; the skill's default is used otherwise. In v0.1 this covers templates; playbook overrides come in v0.4. For config, maps merge, lists replace, and `null` removes a map entry. An override replaces a whole file and records `based_on`. There are no partial patches, because they break silently when the default changes.

**Registers are the single source of truth.** Views and documents are generated from them. The agent never invents facts. Each entry is one line.

**Templates are contracts.** `structure_check` verifies a draft against its doc type's checks, so correctness does not depend on the model remembering the rules.

**House rules** win over the skill's rules, except the safety rules (section 1).

---

## 3. What v0.1 contains

### Engine files to copy (from the source project, then generalise)

| Source file | Becomes | Generalisation needed |
|---|---|---|
| `pmo/skill/SKILL.md` | `SKILL.md` | New generic name and description; spec fields only; no project facts; lists the safety rules; `allowed-tools` for the scripts (3.1, fix 8) |
| `pmo/playbooks/*` (generic ones) | `references/` | Remove project wording and stack-specific paths; drop modes (each request routes straight to a playbook) |
| `pmo/tools/pmo_common.py` | `scripts/pmo_common.py` | Add a `--project` root (default: current folder); path lookup with override search; the Python version check |
| `pmo/tools/render_views.py` | `scripts/render_views.py` | Priority order and date fields from config; validation (3.1, fix 10); deterministic output; `--check` exits 1 when validation fails or views are stale; self-test on fixtures |
| `pmo/tools/structure_check.py` | `scripts/structure_check.py` | Per-type rules keyed by heading names become declared checks (see 3.2); self-test on fixtures; add `--help` |
| `pmo/tools/docs_audit.py` | `scripts/docs_audit.py` | Exit 1 on findings; stale documents by hash (section 1); add `--help` |
| `pmo/tools/overdue.py` | `scripts/overdue.py` | Statuses and severity order from config; window as a flag; fix the crash when `--as-of` has no value |
| The templates Phase B picks | `assets/templates/` | `{{project}}` and `{{manager}}` placeholders |
| The registers Phase B picks, empty | `assets/starter/registers/` | Header comments only |
| (new) | `assets/config.default.yaml` | `schema_version: 1` and only the keys v0.1 reads: doc types, vocab, register fields, `paths` |
| (new) | `scripts/setup.py`, `references/setup.md` | See 3.3 |
| (new) | `scripts/where.py` | See 3.1, fix 14 |
| (new) | `scripts/_vendor/yaml/` | PyYAML's pure-Python package, unchanged, with its licence |
| (new) | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `evals/` (repo root) | See section 5, Plugin |

### Not in v0.1

Generators (`regen_docs`, `scope_wbs`, `decision_log`), `parity_check`, every translation tool, spreadsheet and review tools, PDF merge, graph tools, repo sync, the technical templates, the cheatsheet and portable prompt, the source's pre-commit hook (section 1, Git hook) and playbook overrides.

### 3.1 Fixes carried over from the source review

These bugs and rule conflicts were found in the source and must not be copied across. Each is fixed once, in the shared code or playbook.

1. **One commit model.** Document it in one place (a `git.md` reference). The agent never runs `git add`, `commit` or `push` unless the playbook says so and the user asked.
2. **No `.bak` copies.** Git is the backup.
3. **Do not regenerate unasked.** Governance and tracking steps *list* stale documents and *offer* to regenerate.
4. **Definition of done.** Marking a task done requires QA confirmation or a note saying "no test evidence recorded". The tracking playbook points to the governance rule.
5. **`generated_from` must be complete.** Every register a template reads is listed, otherwise stale-document warnings are wrong.
6. **Config comments match the real values.** Remove unused keys.
7. **Tools:** `docs_audit` exits 1 on findings; every tool has `--help`; `overdue` does not crash on a missing value.
8. **Permissions.** `SKILL.md` lists the scripts in `allowed-tools` in the documented space form with `${CLAUDE_SKILL_DIR}`, for example `Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py *)`. That grant lasts only for the turn that loads the skill, so later turns may ask for permission; the README says so. The `:*` form the source documented is not in the current docs.
9. **One home per rule.** Behaviour rules live only in `SKILL.md`. Other files link to it.
10. **Validation.** Every entry is validated against `vocab` and its register's fields: issue severity, risk probability and impact, and the status of every register. Duplicate ids and multi-line entries fail.
11. **A named "Finish" step.** Copy `template_version`, record the hash of each `generated_from` register, remove HTML comments, run the checks, mark the document finished. Defined once; recipes say "Finish".
12. **Read less.** Each playbook starts with a `Reads:` line naming exactly the files and sections it needs. `SKILL.md` step 1 is "open the playbook for the request", not "read everything".
13. **Edit one entry, not the file.** Each entry is one line; tracking finds it with `grep -n 'id: T-014'` and edits that line.
14. **A `where` tool.** `scripts/where.py <type> [period]` prints the document path, template path, `generated_from` and the winning override. It replaces path rules written in prose and is what makes overrides work.

### 3.2 Per-type checks (open)

`structure_check` today has rules keyed by English heading names, so a renamed section silently turns a check off. In v0.1 each doc type declares `checks:`, with a few named kinds (`required_cells`, `equal_count`, `listed_have_sections`).

**Open, decide before Phase C touches `structure_check`:** where the checks are declared. In `config.yaml` (all checks in one place; an override template means editing two files), or in each template's front matter (an override carries its own checks, which matches the glossary's "skeleton and contract"). Also open: whether a check that names a missing section fails instead of skipping.

### 3.3 Setup

`references/setup.md` tells the agent to:
1. Stop if `pmo/config.yaml` exists (never overwrite). Instead, compare its `schema_version` with the skill's: equal means nothing to do, older means a migration is due (none exist in v0.1), newer means the skill is out of date.
2. Ask a few questions with defaults shown: project name, project manager, week start, priority order.
3. Show the files it will write as a tree and wait for a yes.
4. Run `scripts/setup.py`.
5. Run `render_views.py --check` and say what to do next ("add your first tasks", "draft the project charter"). If the project has a git remote, say in one line that `pmo/` holds people's names.

`scripts/setup.py` does the copying deterministically: a sparse config, the empty registers, `house-rules.md` and `pmo/documents/`. It installs no git hook; it prints the one line a user can add to their own hook to run `render_views --check`. It takes flags so a user can run it without an agent. Unknown values stay `null` and become open questions. It can run more than once and never overwrites.

### 3.4 Privacy scrub (before any file is staged)

Build the repo by **copying engine files into `tmp/source/`** and generalising from there. Never push the source project's history. Before a file is staged, none of these may appear in it:

- Real names and roster slugs, including `owner:` values in templates and self-tests.
- Private repo URLs and machine paths (`/home/`, shell profile files).
- The source project's name, its sub-project ids and its own-language project name.
- Emails, phone numbers and contact details.
- Security issues, permission matrices and auth requirements.
- Snapshot SHAs and branch names.
- Memory files, learning files, scratch folders, inbox and reference folders.
- Any file copied from the maintainer's private notes vault.

`dev/scrub.sh` checks machine paths, emails and phone numbers, plus the names in the untracked `.scrub-names` (every roster slug, full name, sub-project id and project name). It checks the staged copies and untracked files, which is what a commit would publish. It fails when `.scrub-names` is missing, except in CI, which checks the generic patterns only. Security details and project-specific logic are not caught by any pattern: they are removed by reading each file while generalising it. The Phase B inventory names the source's specifics, so it stays in `tmp/`.

---

## 4. Phases

### Phase A: foundation (S)
- Rename the repo and local folder to `pmo-docs` (done).
- Create `skills/pmo-docs/` and the folders above.
- Create `memory.md` in the repo root (local only, never committed).
- Reword the GitHub initial commit to `chore: initial commit` (done 2026-11-04, force-pushed).
- Add the CI workflow (section 1, CI).
- **Done when:** the layout exists, CI passes, and the scaffold is committed with approval (the first commit after the initial commit).

### Phase B: copy into the workspace (S)
- Copy the engine files in 3 into `tmp/source/` inside this repo (gitignored, so nothing there can be staged).
- Read the copied playbooks, tools and `SKILL.md` in full and list what each one hard-codes, in `tmp/inventory.md`. This replaces the earlier grep-based inventory.
- Apply the v0.1 content rule (section 1) to pick the playbooks, recipes, doc types and registers.
- **Done when:** the inventory is written in `tmp/` (it names the source's specifics, so it is never committed), and this plan holds only the generic result: the v0.1 list of playbooks, recipes, doc types and registers, and a confirmed glossary definition of Recipe. Nothing is committed in this phase.

### Phase C: generalise (M-L)
- Move each file from `tmp/source/` into `skills/pmo-docs/` only once it is generic and `dev/scrub.sh` is clean. Commit in small groups, with approval.
- Write `assets/config.default.yaml` from scratch, using the source config only as a reference for the shape.
- Vendor PyYAML into `scripts/_vendor/` and add the Python version check.
- Make priorities, statuses, severity and dates config-driven.
- Settle where checks live (3.2), then move the `structure_check` rules there.
- Apply the fixes in 3.1.
- Replace project names in templates with `{{project}}` and `{{manager}}`.
- Write `setup.md` and `setup.py` (3.3) and `where.py`.
- Add the plugin manifest (section 5, Plugin).
- Trim `SKILL.md`: spec fields only, description under 1024 characters, body under 500 lines, folder name equals `name`, safety rules listed.
- **Done when:** `setup.py` on an empty folder produces a project where render, structure check and audit all pass.

### Phase D: tests (M)
- `tests/` runs only on `examples/acme`, copied into a temp folder. Nothing writes outside a temp folder, and there is no network and no real data.
- Self-tests of `render_views` and `structure_check` use Acme, not live data.
- Cover: setup on an empty folder writes nothing before consent and never overwrites; the priority order is read from config; `docs_audit` exits 1 on findings and reports a stale document after a register changes; every tool answers `--help`; a project with a newer `schema_version` is refused; duplicate ids and multi-line entries fail validation; rendering twice gives identical views; no tool runs `git add`.
- Write the two evals: setup writes nothing before the user says yes; drafting a document from the Acme registers passes its checks.
- **Done when:** everything passes in CI on Python 3.10 and the newest stable release with nothing installed beyond Python, and both evals pass.

### Phase E: docs (S-M)
- README: what it is; install (`/plugin marketplace add` and `/plugin install`, or copy `skills/pmo-docs/` into the agent's skills folder); Linux and macOS (Windows through WSL); Python 3.10+ with nothing to pip install; quick start; what it reads and writes; that it sends nothing and never pushes; the one-writer limit; that `pmo/` holds people's names; how to call `render_views --check` from a git hook; that later turns may ask for permission (3.1, fix 8); and the "Claude Code verified, other agents untested" note.
- The `examples/acme` walkthrough (the same Acme the tests use).
- **Done when:** a new user can follow the README from nothing to a first rendered view.

### Phase F: release v0.1 (S-M)
- Write `dev/release`, a shortcut modelled on the release script of the maintainer's `jekyll-theme-resume` repo. Usage: `dev/release [--bump] [version]`.
  1. Refuse to run with uncommitted changes, unless `--allow-dirty`.
  2. Run `dev/scrub.sh`, the tests and `claude plugin validate . --strict`. Stop on any failure.
  3. Pick the version: the argument, or `git-cliff --bumped-version` with `--bump`.
  4. Write the version into `SKILL.md` (`metadata.version`) and `.claude-plugin/plugin.json`.
  5. Run `git-cliff -o CHANGELOG.md --tag vX.Y.Z` and print the new release notes. The same text for a GitHub release comes from `git-cliff --latest --strip header`.
  6. Ask for confirmation, default **No**. There is no `-y` flag, because commits and pushes need the maintainer's approval.
  7. Commit `chore(release): vX.Y.Z`, create an annotated tag, and push the branch and tag.
- Changelog config is `cliff.toml`: Keep a Changelog groups mapped from conventional prefixes, internal commit types left out, commit-hash links, compare-link footer, 0.x-safe version bumps (a breaking change bumps the minor). No GitHub API calls. Because the repo is public, every commit subject becomes a public changelog line, and `dev/scrub.sh` checks subjects for blocked names.
- It lives in `dev/`, not `bin/`: a plugin's `bin/` is put on the Bash tool's PATH, so a maintainer script there would ship to every user.
- Run the evals by hand and scan the finished skill with SkillSpector (NVIDIA's open-source static scanner for agent skills; needs Python 3.12+; use the static scan, since its LLM mode was reported not to work with the Anthropic API). Then run `dev/release 0.1.0`. This release commits `CHANGELOG.md` for the first time.
- The repo is public from the start (section 7), so the release adds the tag and the GitHub release only.

---

## 5. Later releases

Roadmap. One theme per minor version, each about M-sized.

| Version | Theme |
|---|---|
| v0.1 | Core skill and plugin manifest (sections 3 and 4) |
| v0.2 | Generators, calendar, publish target with the `init` and `publish` commands, override drift warning, generated catalogue, cheatsheet and portable prompt |
| v0.3 | Languages and translation, `parity_check`, intake |
| v0.4 | Stacks, playbook overrides with versions, the technical and domain templates; optional integrations |
| v0.5 | Tested on other agents |
| 1.0 | The config schema has not changed for two minor versions, and an upgrade from every 0.x release is tested |
| After 1.0 | Team support: ids that cannot collide, a hook shared through the repo |

Every release that changes the config or register format bumps `schema_version`, ships a migration script and a CHANGELOG upgrade note.

### v0.2 to v0.4 details
- **Languages** (v0.3). Config names the draft language and any number of translations:
  ```yaml
  languages:
    draft: en
    translations: [ar]       # [] = English only
    en: { label: EN, dir: ltr }
    ar: { label: AR, dir: rtl, digits: arabic-indic, glossary: pmo/data/glossary-ar.md }
  ```
  A doc type's languages default to the draft plus the translations. A per-type flag `translate: in-period | after-close` says when translation happens. Finish loops over the translations and reads that flag. `parity_check` reads each language's digits and connector words from config. Translation glossaries are split into an approved file and a proposed file; Finish reads the first and only appends to the second.
- **Generators** (v0.2). One `scripts/generate.py` with a subcommand per document type and `--period` and `--week` flags. Each doc type may name a `generator:` in config; the draft playbook runs it and the agent edits only the prose. Shared helpers come from `pmo_common` (one roster parser, one table writer that escapes `|`, one RAG function used by the playbook, the script and the prompt). The weekly snapshot is written by the script, not by hand.
- **Stacks** (v0.4). `draft-technical.md` stays generic (inventory, read the code, fan out, record findings). `references/stacks/<stack>.md` says where routes, pages and screens live for one stack. Start with a few examples. For an unknown stack, the agent asks and writes a new stack file into the project's `pmo/playbooks/stacks/`. This is why playbook overrides arrive in v0.4, with a `playbook_version` and `based_on` like templates.
- **Technical and domain templates** (v0.4). The lifecycle type becomes `entity-lifecycle`, with the entity named in config (`domain.lifecycle_entity`). Permission roles come from `domain.roles`. Consumer columns in the integration guide come from the sub-projects that call the API.
- **Intake** (v0.3). Reads any chat export, not one specific app. Done work goes in as dated done-history tasks, with the user's confirmation. Credentials never enter the registers.
- **Publish target** (v0.2, config):
  ```yaml
  publish: { mode: repo, path: documentation, url: null }   # repo | folder | none
  ```
  `repo` copies finished documents and commits in a separate docs repo (the user pushes). `folder` copies them into a folder of the same repo and leaves the commit to the user. `none` keeps the finished documents where they are.
- **Calendar** (v0.2). `week_start`, period and priority order come from config.
- **Override drift warning** (v0.2). Overrides record `based_on: <type>@<version>` from v0.1. From v0.2, when the default template moves to a newer `template_version`, `docs_audit` warns.
- **Generated catalogue** (v0.2). "Generate when" and "regenerate when" live in config per doc type, and `render_views` writes the catalogue and the portable prompt from them.
- **Optional integrations** (v0.4; graph tools, scheduled refresh, repo sync): documented, off by default.
- **Other tools** (v0.2): the cheatsheet, the portable prompt generator, `sync_repos` (optional).
- **Extras that stay out unless generalised:** spreadsheet review tools, work-order and PDF tools. Decide per tool when v0.2 starts.

### Plugin (manifest from v0.1)

- **Files**, added at the repo root (the skill folder does not move):
  ```
  .claude-plugin/plugin.json       v0.1  name, version, description, author, license, homepage, repository
  .claude-plugin/marketplace.json  v0.1  one entry: this plugin, source "./"
  evals/                           v0.1  `claude plugin eval` cases
  skills/init/SKILL.md             v0.2  disable-model-invocation: true, follows references/setup.md
  skills/publish/SKILL.md          v0.2  disable-model-invocation: true, follows references/publish.md
  ```
  No `hooks/`, `bin/` or `requirements.txt`: PyYAML is vendored, and `allowed-tools` covers permissions.
- `plugin.json`: `"license": "MIT"`, `name` is `pmo-docs`. `dev/release` writes the version to both `plugin.json` (read by plugin installs) and `SKILL.md` `metadata.version` (read by skill-only installs). Never in `marketplace.json`, where a second copy would drift.
- `init` and `publish` (v0.2) run only when the user types them, so the model can never start a publish on its own. Commands are namespaced: `/pmo-docs:init`, `/pmo-docs:publish`. Installed as a plugin, the main skill is `/pmo-docs:pmo-docs`.
- **Script paths:** `python3 "${CLAUDE_SKILL_DIR}/scripts/render_views.py"`. `${CLAUDE_SKILL_DIR}` is substituted in the text of `SKILL.md`, not set in the Bash environment. Scripts also find their own folder through `__file__` and default the project to the current folder, because other agents lack the variable.
- **Evals:**
  1. (v0.1) Setup in an empty folder writes nothing before the user says yes.
  2. (v0.1) Drafting a document from the Acme registers passes its checks.
  3. (later) "T-001 is done" asks for the definition of done when QA is needed.
  4. (v0.2) The model refuses to publish on its own.
- **Done when (v0.1):** `claude plugin validate . --strict` passes and `claude --plugin-dir .` drafts a document in `examples/acme`.
- **Install, for users:**
  ```
  /plugin marketplace add <owner>/pmo-docs
  /plugin install pmo-docs@pmo-docs
  ```
  Update with `claude plugin update pmo-docs@pmo-docs`. Auto-update is off for marketplaces that are not Anthropic's, so say so in the README. Pin a version with `/plugin marketplace add <owner>/pmo-docs#v0.1.0`.
- **Versioning:** see the roadmap table at the top of this section.
- **Optional, later:** submit to the Anthropic directory (needs a paid plan, a README and a LICENSE, files under 256 KiB, at most 512 files, no symlinks or binaries, pinned launchers and a passing security scan). A generic name like `pmo-docs` may be held for review. The vendored PyYAML is 17 files, the largest about 50 KB.

### v0.5: other agents
After the skill is stable, test the `skills/pmo-docs/` folder in other agents (Codex, Gemini CLI, Cursor, Copilot). Until then it is not claimed to work.

---

## 6. Open decision: the source project

After v0.1, the source project may either:

| | Migrate to this skill | Stay separate |
|---|---|---|
| What changes | It keeps its project parts (config, registers, data, house rules) and its real overrides, and deletes its own engine copies. | Nothing. |
| Cost | About one session plus checks. Template and hook paths move. | Every fix is made twice and the copies drift. |
| Gain | One engine; a fix helps every project. | No change now. |

Decide after v0.3. Until then there is no sync (section 1).

---

## 7. Public repo safeguards and release checklist

The repo is public, so every commit, message and file is visible. Rules that keep it safe:

- **Commit gate on every clone:** `git config core.hooksPath .githooks`. The pre-commit hook runs `dev/scrub.sh`; the commit-msg hook blocks blocked names in subjects. Never bypass with `--no-verify`.
- **`.scrub-names` is complete before Phase B:** roster slugs, full names (also in other scripts, such as Arabic), sub-project ids and project names. The file stays untracked; without it the scrub fails (except in CI).
- **Raw copies never get staged.** They live in the gitignored `tmp/source/`; files move into the skill one at a time once generic, and the scrub runs before each commit.
- **If a leak is committed anyway:** treat the data as exposed. Rotate any credential, and rewrite history only with the maintainer's approval. Deleting the file in a later commit does not remove it from history.

Release checklist (v0.1):

- [ ] `dev/scrub.sh` clean, including the local-only name list (3.4)
- [ ] `claude plugin validate . --strict` passes
- [ ] Both evals pass
- [ ] SkillSpector scan has no findings
- [ ] `LICENSE` (MIT) present and `license` set in `plugin.json`
- [ ] README states what is read and written, that nothing is sent, that nothing is pushed, and that `pmo/` holds people's names
- [ ] Tests pass on a clean machine
- [ ] Git history reviewed for private data (`git log -p` through the scrub patterns)
- [ ] The maintainer approves

---

## 8. Limits

- Facts below come from the Claude Code plugin and skills docs, the Agent Skills spec, PEP 619 and PEP 668, read on 2026-10-20 and 2026-11-04.
- Verified on 2026-11-04: `${CLAUDE_SKILL_DIR}` is substituted in `SKILL.md` text and in `allowed-tools`; an `allowed-tools` grant lasts for the turn that loads the skill; a plugin's install path changes on every update; a plugin's `bin/` is on the Bash tool's PATH only; `${CLAUDE_PLUGIN_DATA}` survives updates; a plugin can be just a manifest plus `skills/`; SkillSpector is NVIDIA's open-source static scanner; Python 3.10 reached end of life on 2026-10-01.
- Not verified:
  - registry tools in the `npx skills` style
  - where Codex, Gemini CLI and Cursor look for skill folders
  - whether claude.ai and Cowork load this plugin
  - marketplace naming rules and collision behaviour (not covered by the pages read)
  - how Claude chooses between installed skills with overlapping descriptions
  - Bash permission rules with `~` or wildcards inside a path
  - PEP 668 refusals on specific Debian, Ubuntu and Homebrew releases, and stock macOS `python3` being 3.9.6 (secondary sources only)
- Other agents do not have `${CLAUDE_SKILL_DIR}`. The fallback is `__file__` plus the current folder.
- Token and size figures for the source skill were byte counts divided by 4 and are rough.

---

## 9. Naming rules (checked 2026-11-04)

- **Skill `name`:** 1-64 characters; lowercase letters, digits and hyphens; no leading or trailing hyphen; no `--`; must equal the parent folder name. `description` is 1-1024 characters, says what it does and when to use it, leads with the use case, and includes trigger words. Keep `SKILL.md` under 500 lines.
- **Plugin `name`:** kebab-case; no spaces, `@`, `:`, path separators or control characters. It must not start with `claude-`, `anthropic-`, `anthropics-` or `cc-plugin-`, and must not be exactly `claude`, `anthropic`, `anthropics`, `claude-code` or `claude-mods`. `claude plugin validate` checks these.
- The repo name does not have to match the plugin name; we keep them equal anyway.
- `pmo-docs` passes all of these.
- Claude Code does not require the skill `name` to equal its folder, but the open spec does, so keep them equal.

Sources:
- https://agentskills.io/specification
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/plugins/manifest-reference.md
- https://code.claude.com/docs/en/plugins/publish.md
- https://claude.com/docs/plugins/pre-submission-checklist

---

## 10. Checklist

- [ ] Phase A: rename to `pmo-docs` (done), layout, `memory.md`, initial commit reworded (done), CI workflow, scaffold committed
- [ ] Phase B: engine copied into `tmp/source/`, inventory in `tmp/`, v0.1 content list in this plan
- [ ] Phase C: sparse generic config with `schema_version`, vendored PyYAML, config-driven priorities, checks declared (3.2), 3.1 fixes, templates with placeholders, setup, `where`, plugin manifest, trimmed `SKILL.md`, committed in small groups (with approval)
- [ ] Phase D: tests on `examples/acme`, CI on Python 3.10 and the newest stable, two evals
- [ ] Phase E: README, Acme walkthrough
- [ ] Phase F: `dev/release` script, plugin validate, evals, SkillSpector scan, release `v0.1.0`
- [ ] v0.2: generators, calendar, publish modes with the `init` and `publish` commands, override drift warning, catalogue
- [ ] v0.3: languages, `parity_check`, intake
- [ ] v0.4: stacks, playbook overrides, technical and domain templates
- [ ] v0.5: test on other agents
- [ ] 1.0: config schema stable, upgrades from every 0.x tested
- [ ] After 1.0: team support
- [ ] Decide: where checks live (3.2), before Phase C touches `structure_check`
- [ ] Decide: the source project's path (section 6)
- [x] Decided: public from the start (section 7)
- [x] Decided: roadmap, schema version, tests and CI, raw-copy workspace, changelog rules, glossary, documents folder (sections 1 and 3.3, 2026-11-04)
- [x] Decided in the second review (2026-11-04): ownership, plugin manifest in v0.1, vendored PyYAML, Python 3.10 with a clear message, Linux and macOS, one writer and team-safe, no user-project hook, committed views, sparse config, v0.1 content rule, one-line entries, template-only overrides with `based_on`, house-rule precedence, stale by hash, `pmo/documents/`, evals in v0.1, CI from the first commit, v0.4 dissolved (section 1)
