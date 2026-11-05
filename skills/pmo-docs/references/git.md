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

Everything under `pmo/` is tracked and never ignored: the config, registers, views, documents, templates and house rules. Views are committed so that others can read them without running anything. Registers keep one entry per line, so a changed entry is a one-line diff. After a merge conflict in a view, render it again with `render_views.py`.

## When the user asks to commit

1. Run `git status -sb` and propose the commit groups: for example registers with the views rendered from them, then each document on its own. Wait for the user's answer.
2. Stage the named paths one by one (`git add <path> ...`) as `SKILL.md` says. If a path is already staged by the user, say so before adding more.
3. Commit with a one-line subject. If a hook rejects the commit, report why.
4. Do not push. Push only when the user asks for exactly that.

## Checking registers in your own hook

The skill installs no hook. A project that wants one writes its own, because the skill's folder is at a different path on each machine and changes when a plugin updates. `render_views.py --check` is made for it: it writes nothing, stages nothing, and exits 1 when the registers fail validation or a view is stale. Needs Python 3.10 or newer.

```sh
#!/bin/sh
# .git/hooks/pre-commit - set PMO_DOCS to the skill folder on this machine
PMO_DOCS=/path/to/skills/pmo-docs
python3 "$PMO_DOCS/scripts/render_views.py" --project "$(git rev-parse --show-toplevel)" --check || {
  echo "pmo: fix the registers, or run render_views.py to refresh the views, then commit again" >&2
  exit 1
}
```

Make it executable. A hook in `.git/hooks` is not shared with teammates; to share one, keep it in a tracked folder and set `git config core.hooksPath <folder>` in each clone.
