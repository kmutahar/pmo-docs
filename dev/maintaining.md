# Maintainer tasks

Not shipped. Linked from [`AGENTS.md`](../AGENTS.md) (which holds the standing repo rules). Script usage is in each script's `--help`.

## Checks

### Evals (heavy check)
- Command: `dev/run-evals [--case <name>]... [--runs N] [--jobs N] [--out DIR]` (all cases, 4 at once, Sonnet as agent and judge; estimated ~$5 for a full run; Haiku fails 5 of 9 and splits judge votes).
- Output folder: `~/pmo-eval-runs/<UTC time>/` holding `summary.log`, a throwaway plugin copy, and per case: `eval.log`, `report.html`, `aggregate-result.json`, and `sandbox-<n>/` (never run git inside a sandbox).
- Why a throwaway copy: the plugin root is `skills/pmo-docs` and `claude plugin eval` needs `evals/` inside the plugin; running `claude plugin eval` from the repo root never fires the skill.
- Single samples can flip: re-run a failing case before changing `SKILL.md`.
- Authoring rules: pin today's date in prompts; name output files in prompts; `llm` graders see paths, not file text (unless `focus: {source: file}` is used); `max: 0` needs `min: 0`; keep grader text short and positive. Bash fails in the eval sandbox (`apply-seccomp ... setgroups`), so graders must not rely on Bash; `dontAsk` mode denies Glob/Grep in the skill folder, so playbooks name skill files by exact `${CLAUDE_SKILL_DIR}/...` path.

### SkillSpector (heavy check)
- Scan a clean copy of tracked files (a tree with `__pycache__` gives false findings):
  ```sh
  SKILLSPECTOR_PROVIDER=claude_cli SKILLSPECTOR_MODEL=sonnet skillspector scan skills/pmo-docs --baseline dev/skillspector-baseline.yaml
  ```
- A valid result is `SAFE` with full coverage and all LLM calls succeeded (`llm_calls_succeeded`); a cut-off run is not a result.
- Haiku produces false positives on vendored PyYAML. Avoid apostrophes in `config.default.yaml` comments (they break the static parser). Every baseline entry needs a reason.

### Install, walkthrough and agent checklists
- **Install check:** [`dev/test-install.md`](test-install.md) — Parts 1–3 before a tag (local marketplace), Part 4 on the published release zip; uses a throwaway `CLAUDE_CONFIG_DIR`.
- **Walkthrough check:** [`dev/test-walkthrough.md`](test-walkthrough.md) — runs [`docs/walkthrough.md`](../docs/walkthrough.md) commands and prompts in a throwaway `CLAUDE_CONFIG_DIR`; keep both files in step.
- **Other-agent trials:** [`dev/agent-trial.md`](agent-trial.md) — trials Codex, Gemini CLI, Cursor and Copilot.

### Updating vendored PyYAML
- Run `dev/update-pyyaml <unpacked sdist>` (script header has the steps; `dev/pyyaml-prune.patch` is the cut; edit `skills/pmo-docs/scripts/_vendor/VERSION` by hand).

## Working on a version

Rules in [`AGENTS.md`](../AGENTS.md) apply in full.
- Check the plan against the working tree before any package starts.
- Packages run sequentially; parallel only when the plan says so and their "Touches" lists do not overlap.
- A package is done when its "Done when" list, unit tests and `bash dev/scrub.sh` pass. Per-package reviews are skipped in favour of one whole-tree review before release.
- Each package carries its own docs (`SKILL.md`, `references/conventions.md`, `GLOSSARY.md`). `README.md` rewording waits for a docs pass.
- Test files follow `tests/test_render_views.py` (`unittest`, `subprocess` + `sys.executable` on a temp copy of `examples/acme`, first-line docstring stating what it tests and how to run it).
- Unfinished work moves to the next plan or a `<version>-skipped.md` note.

## Release checklist

1. All packages committed on `dev` in order, with approval; cleanup in its own commit before `dev/release`.
2. `python3 -m unittest discover tests` and `bash dev/scrub.sh` pass; CI is green on `dev`.
3. `claude plugin validate .` and `claude plugin validate skills/pmo-docs` exit 0 (`dev/release` prints warnings and stops only on failure; read warnings); plugin listing shows each skill once.
4. Dry runs: `dev/release --bump --dry-run`, then `dev/release --dry-run X.Y.Z` (in 0.x `--bump` proposes minor for `feat`/breaking, patch otherwise). Verify the changelog reads well and has no private names or machine paths.
5. Release (maintainer only): `dev/release X.Y.Z` (asks twice at the terminal; steps in `dev/release --help`).
   - The release commit holds only `CHANGELOG.md` and the four version files (`skills/pmo-docs/SKILL.md`, `skills/pmo-docs/.claude-plugin/plugin.json`, `README.md`, `docs/INSTALL_FOR_AGENTS.md`).
   - It pushes `dev` and the `v*` tag. `.github/workflows/release.yml` builds the release (fails if the changelog section is missing), then its `fast-forward-main` job moves `main` to the tag. Never commit to `main` directly or that job fails.

## Never in a tracked file or a commit message

Real names and roster slugs (including `owner:` values in templates and fixtures); private repo URLs and machine paths; the source project's name and ids; emails, phone numbers and contact details; security issues, permission matrices and auth requirements from the source; snapshot SHAs and branch names from the source; contents of memory files, scratch folders or private notes. Learnings (`.trail/learnings/`) are local and untracked, and hold rules only. `dev/scrub.sh` catches patterns only: read each file when generalising, and rewrite anything taken from `tmp/source/` from scratch.

## Platform limits

- **Verified:**
  - `${CLAUDE_SKILL_DIR}` is substituted in `SKILL.md` text and `allowed-tools`; `${CLAUDE_PLUGIN_ROOT}` is substituted in skill text.
  - An `allowed-tools` grant lasts for the turn that loads the skill; `disable-model-invocation: true` keeps a skill's description out of context and blocks model invocation.
  - Plugin `skills` paths must start with `./` and stay inside the plugin root; a plugin can be just a manifest plus `skills/`; its install path changes on every update; its `bin/` is on the Bash tool's `PATH` only; `${CLAUDE_PLUGIN_DATA}` survives updates.
  - Codex and Antigravity read skills from `~/.agents/skills`.
  - `npx skills add . --list` discovers only `pmo-docs` (`metadata.internal: true` hides `skills/init` and `skills/publish`).
- **Not verified:** whether default `skills/` is scanned in addition to listed paths, and whether `"./"` loads nested skill folders by itself; end-to-end `npx skills add`/`update` across agents; where Gemini CLI, Cursor and Copilot look for skills; claude.ai and Cowork loading; marketplace naming collisions; Claude's choice between overlapping skill descriptions; Bash permission rules with `~` or wildcards; PEP 668 refusals on specific distros and stock macOS `python3` 3.9.6.
- **Anthropic directory (optional):** requires a paid plan, `README.md`, `LICENSE`, files under 256 KiB, at most 512 files, no symlinks or binaries, pinned launchers and a passing security scan. A generic name may be held for review. The listing icon (`dev/icon-brief.md`) is locked on the first developer-portal submission.

## Naming rules

- **Skill `name`:** 1–64 chars; lowercase letters, digits, hyphens; no leading/trailing hyphen or `--`; equals parent folder name. `description` is 1–1024 chars, leads with use case and trigger words. Keep `SKILL.md` under 500 lines.
- **Plugin `name`:** kebab-case; no spaces, `@`, `:`, path separators or control chars; must not start with `claude-`, `anthropic-`, `anthropics-` or `cc-plugin-`; must not equal `claude`, `anthropic`, `anthropics`, `claude-code` or `claude-mods`. Checked by `claude plugin validate`.
- Sources: agentskills.io/specification and Claude Code docs (skills, plugin manifest, components, publishing).
