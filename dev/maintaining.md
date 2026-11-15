# Maintainer tasks

Not shipped. Linked from `AGENTS.md`. Script usage is in each script's `--help`.

- **Evals** (heavy check: runs in the verification release; the cases in `evals/`, real agent runs, an estimated $5 for all on Sonnet with a Sonnet judge): `dev/run-evals [--case <name>]... [--runs N] [--jobs N] [--out DIR]` (all cases, 4 at once, Sonnet as agent and judge; the Haiku default judge splits its votes). Everything stays in one folder, `~/pmo-eval-runs/<UTC time>/`: `summary.log`, the plugin copy, and per case `eval.log`, `report.html` (the judges' reasons), `aggregate-result.json` and `sandbox-<n>/` (trace, session transcript, the project as the agent left it; never run git inside it). It builds a throwaway plugin copy because the plugin root is `skills/pmo-docs` and `claude plugin eval` needs `evals/` inside the plugin; plain `claude plugin eval` from the repo root never fires the skill. Use Sonnet (Haiku fails 5 of 9). Results are single samples and can flip, so re-run a failing case before changing `SKILL.md`. Prompts pin today's date. Grader lessons: an `llm` grader sees a file's path, not its text; `max: 0` needs `min: 0`; keep grader text short and positive; name output files in the prompt. Bash fails in the eval sandbox (`apply-seccomp ... setgroups`), so the agent cannot run the scripts and graders must not depend on Bash; the agent also runs in `dontAsk` mode, which denies Glob and Grep in the skill folder, so a playbook must name skill files by their exact `${CLAUDE_SKILL_DIR}/...` path.
- **SkillSpector** (heavy check: runs in the verification release): scan a clean copy of the tracked files (a tree with `__pycache__` gives false findings) with `SKILLSPECTOR_PROVIDER=claude_cli SKILLSPECTOR_MODEL=sonnet skillspector scan skills/pmo-docs --baseline dev/skillspector-baseline.yaml`. A real result is SAFE with full coverage and every LLM call succeeded (`llm_calls_succeeded`); a cut-off run is not a result. Haiku reports false positives on the vendored PyYAML. Each LLM call is a `claude` session on the maintainer's plan. Avoid apostrophes in `config.default.yaml` comments (they break the static parser). Every baseline entry needs a reason.
- **Updating vendored PyYAML:** `dev/update-pyyaml <unpacked sdist>` (header has steps; `dev/pyyaml-prune.patch` is the cut; `_vendor/VERSION` is edited by hand).
- **Install check** (runs before the tag against a local marketplace, and Part 4 on the release zip; heavy checks run in the verification release — see `dev/test-install.md`): `dev/test-install.md`, in a throwaway `CLAUDE_CONFIG_DIR`.
- **Walkthrough check** (heavy check: runs in the verification release): `dev/test-walkthrough.md`, in a throwaway `CLAUDE_CONFIG_DIR`. It runs the walkthrough's commands and the agent prompts; keep it in step with `docs/walkthrough.md`.

## Working on a version

- Rules from `AGENTS.md` apply in full. Check the plan against the working tree before any package starts.
- Packages go one after another; parallel only when the plan says so and their "Touches" lists share no file. The drafting agent may be another tool; it leaves the changes in the working tree.
- A package is done when its "Done when" list passes, including `python3 -m unittest discover tests` and `bash dev/scrub.sh`. Per-package reviews are not run: one Opus-high review over the whole tree runs once, in the verification release, before 1.0.
- A package carries its own docs with its code and tests, including shared docs (`SKILL.md`, `references/conventions.md`, `GLOSSARY.md`). Rewording of `README.md` waits for a docs pass.
- Tests: `unittest`, a temp copy of `examples/acme`, the script run with `subprocess` and `sys.executable`, nothing written outside the temp folder. The file's first line is a docstring that says what it tests and how to run it.
- Each package names its commit subject. The maintainer commits in package order with `git commit -- <paths>`.
- Unfinished work goes to the next plan or to a `<version>-skipped.md` file the maintainer decides on.

## Release checklist

- Every package is committed in order, with approval.
- `python3 -m unittest discover tests` and `bash dev/scrub.sh` pass; CI is green on `main`.
- `claude plugin validate .` and `claude plugin validate skills/pmo-docs` exit 0 (`dev/release` prints warnings and stops only on a failure; read them); the plugin listing shows each skill once.
- `dev/release --bump --dry-run`, then `dev/release --dry-run X.Y.Z`, then `dev/release X.Y.Z` (in 0.x `--bump` proposes a minor for `feat` and breaking commits, a patch otherwise).
- The dry run's changelog section reads well and holds no private names or machine paths.
- The README roadmap, if it lists the version, is updated.
- Cleanup goes in its own commit before `dev/release`; the release commit then holds only `CHANGELOG.md` and the version files.
- The maintainer approves, commits, tags and pushes (`dev/release` asks twice).

## Never in a tracked file or a commit message

Real names and roster slugs (including `owner:` values in templates and fixtures); private repo URLs and machine paths; the source project's name and ids; emails, phone numbers and contact details; security issues, permission matrices and auth requirements from the source; snapshot SHAs and branch names from the source; contents of the maintainer's memory files, scratch folders or private notes. Learnings (`.trail/learnings/`) are committed, so they hold rules only. `dev/scrub.sh` catches patterns only: security details and project-specific logic are removed by reading each file while generalising it, and anything taken from `tmp/source/` is rewritten from scratch.

## Limits (docs read 2026-10-20, 2026-11-04 and 2026-11-06)

- Verified: `${CLAUDE_SKILL_DIR}` is substituted in `SKILL.md` text and in `allowed-tools`; an `allowed-tools` grant lasts for the turn that loads the skill; a plugin's install path changes on every update; a plugin's `bin/` is on the Bash tool's PATH only; `${CLAUDE_PLUGIN_DATA}` survives updates; a plugin can be just a manifest plus `skills/`.
- Verified in v0.2: plugin `skills` paths must start with `./` and stay inside the plugin root; `disable-model-invocation: true` keeps a skill's description out of context and blocks the model from invoking it; `${CLAUDE_PLUGIN_ROOT}` is substituted in skill text.
- Verified in the v0.5 trials (2026-11-11): Codex and Antigravity read skills from `~/.agents/skills`.
- Not verified: whether the default `skills/` folder is scanned in addition to the listed paths, and whether `"./"` loads nested skill folders by itself (the command skills work as installed); `npx skills`-style registry tools; where Gemini CLI, Cursor and Copilot look for skills; whether claude.ai and Cowork load this plugin; marketplace naming rules and collisions; how Claude chooses between installed skills with overlapping descriptions; Bash permission rules with `~` or wildcards in a path; PEP 668 refusals on specific Debian, Ubuntu and Homebrew releases, and stock macOS `python3` being 3.9.6 (secondary sources only).
- Anthropic directory (optional, 1.0): needs a paid plan, a README and a LICENSE, files under 256 KiB, at most 512 files, no symlinks or binaries, pinned launchers and a passing security scan. A generic name may be held for review. The listing icon can only be set at the first developer-portal submission.

## Naming rules (checked 2026-11-04)

- **Skill `name`:** 1-64 characters; lowercase letters, digits and hyphens; no leading or trailing hyphen; no `--`; equals the parent folder name. `description` is 1-1024 characters, says what it does and when to use it, leads with the use case, and has trigger words. Keep `SKILL.md` under 500 lines.
- **Plugin `name`:** kebab-case; no spaces, `@`, `:`, path separators or control characters; must not start with `claude-`, `anthropic-`, `anthropics-` or `cc-plugin-`; must not be exactly `claude`, `anthropic`, `anthropics`, `claude-code` or `claude-mods`. `claude plugin validate` checks these.
- Sources: agentskills.io/specification and the Claude Code docs pages for skills, plugin manifest, components and publishing.
