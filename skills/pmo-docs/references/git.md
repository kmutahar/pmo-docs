---
playbook_version: 1
---

Reads: nothing else; this is the whole commit model.

# Git

One model for every playbook. The rule itself is in `SKILL.md` (Safety rules, 1).

## What the agent never does

The list of commands the agent never runs unasked is in `SKILL.md` (Safety rules, 1). No script in this skill runs git or installs a hook. Git is the backup.

## What the agent may read

Read-only commands, for evidence and for the state of the project:

- `git status -sb`
- `git log --since=<date> --until=<date> --no-merges --pretty=format:'%h|%ad|%an|%s' --date=short`
- `git log -1 --format=%cs -- <path>` and `git log -1 --oneline`
- `git diff --stat <a>..<b>` and `git show --stat <sha>`
- `git rev-parse HEAD`, `git tag --list`

Reports that use history say "local history as of <date>": the remote may be ahead. Git history alone never changes a status (`SKILL.md`, Working rules).

## What belongs in git

Everything under `pmo/` is tracked, except `pmo/.me` (the writer's own slug, ignored by `pmo/.gitignore`): the config, registers, views, documents, templates and house rules. Views are committed so that others can read them without running anything. Registers keep one entry per line, so a changed entry is a one-line diff. After a merge conflict in a view, render it again with `render_views.py`.

## When the user asks to commit

1. Run `git status -sb` and propose the commit groups: for example registers with the views rendered from them, then each document on its own. Wait for the user's answer.
2. Stage the named paths one by one (`git add <path> ...`) as `SKILL.md` says. If a path is already staged by the user, say so before adding more.
3. Commit with a one-line subject. If a hook rejects the commit, report why.
4. Do not push. Push only when the user asks for exactly that.

The publish command's `repo`-mode commit follows `SKILL.md` Safety rule 1 (`references/publish.md`).


## Checking registers in your own hook

The skill installs no hook. A project that wants one writes its own. The project launcher `pmo/bin/pmo render_views --check` is made for it: it finds the installed skill automatically without hardcoding machine-specific paths, writes nothing, stages nothing, and exits 1 when the registers fail validation or a view is stale. Needs Python 3.10 or newer.

```sh
#!/bin/sh
# .git/hooks/pre-commit
ROOT="$(git rev-parse --show-toplevel)"
"$ROOT/pmo/bin/pmo" render_views --check || {
  echo "pmo: fix the registers, or run render_views to refresh the views, then commit again" >&2
  exit 1
}
```

Make it executable. A hook in `.git/hooks` is not shared with teammates; to share one, keep it in a tracked folder (such as `.githooks/pre-commit`) and set `git config core.hooksPath <folder>` in each clone.


## Several writers

- **Registers:** for a conflict, keep both sides' new lines and delete the marker lines; for an entry changed on both sides, show both lines and ask which to keep (`SKILL.md`, Working rules "Ask, do not guess") before deleting the marker lines around it; then run `render_views.py`. For a duplicate id, run `renumber.py` (`references/track.md`).
- **Views:** never merged by hand; render again.
- **Drafts:** resolve by hand, then `structure_check.py`.
- **Finished documents:** never merged; a second finished version is a new draft.

A GitHub Actions workflow can run the same check as the hook. It downloads the skill at the installed version (`metadata.version` in `SKILL.md`) from the release archive and sets `PMO_DOCS_SKILL` to its `skills/pmo-docs` folder. It runs `pmo/bin/pmo render_views --check` on pushes and pull requests that touch `pmo/**`, with `permissions: contents: read`. It never commits. The workflow (replace `<version>` with `metadata.version` from `SKILL.md`):

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
      - run: curl -fsSL https://github.com/kmutahar/pmo-docs/archive/refs/tags/v<version>.tar.gz | tar -xz
      - run: pmo/bin/pmo render_views --check
        env: { PMO_DOCS_SKILL: pmo-docs-<version>/skills/pmo-docs }
```
