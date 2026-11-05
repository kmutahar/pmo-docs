# Test the README install commands in a throwaway session

A maintainer checklist, not shipped as part of the skill's behaviour. It checks that a stranger can follow the README's **Install** section: add the marketplace, install the plugin, and get a working skill. Nothing here touches your real Claude Code setup if you follow Part 1.

All parts were run and verified on 2026-11-05 (Claude Code 2.1.318, Linux), the live session (steps 11 to 13) by the maintainer: the skill fired from the installed plugin, asked for name, manager and priority order, wrote `pmo/` only after the yes, added a task, and rendered the views.

You need: Claude Code (`claude --version` prints a version), `git`, `python3` 3.10 or newer, and an internet connection (the install pulls the repo from GitHub). Time: about 15 minutes.

Run the check against the **pushed** repo on GitHub, because that is what a user installs. Unpushed changes are not tested.

```
cd ~/github/pmo-docs
git fetch origin
git status -sb          # the first line must read "## main...origin/main" with no "ahead"
```

## How the output is captured (so you can share it)

Every command below is written as `... 2>&1 | tee -a "$LOG/transcript.txt"`. That prints the output on screen **and** appends it to one transcript file. The `claude --debug-file "$LOG/NAME.log"` form (the flag goes before `plugin`) also writes Claude Code's detailed debug log for that one command. At the end you share the folder `$LOG` (Part 4, step 17).

The commands already print each stage on their own (cloning, validating, installing). For machine-readable output add `--json` to `claude plugin list`, `install`, `update` or `uninstall`.

## Part 1: a throwaway Claude Code home

Claude Code keeps its settings, marketplaces and installed plugins in one folder (`~/.claude` by default). The variable `CLAUDE_CONFIG_DIR` points it somewhere else. A temporary folder gives you a clean Claude Code that has never heard of `pmo-docs`, and deleting the folder undoes everything.

1. Make the folders: a fake Claude home, a scratch project, and a folder for the logs.
   ```
   export TRY=$(mktemp -d -t pmo-install-XXXXXX)
   mkdir -p "$TRY/claude-home" "$TRY/project" "$TRY/logs"
   export LOG="$TRY/logs"
   echo "$TRY"
   ```
   Keep this terminal open: `TRY` and `LOG` only exist in it. If you close it, the folder is still in `/tmp`: run `ls -d /tmp/pmo-install-*` and set `TRY` again by hand.

2. Point Claude Code at the throwaway home and go to the scratch project:
   ```
   export CLAUDE_CONFIG_DIR="$TRY/claude-home"
   cd "$TRY/project"
   ```
   Everything from here on, in this terminal only, uses the fresh home. Other terminals are not affected. To use a second terminal later, run these three lines there too (`TRY`, `LOG` and `CLAUDE_CONFIG_DIR`, then the `cd`), with the same paths.

3. Record the environment, then check that it is really clean:
   ```
   { date; uname -a; claude --version; python3 --version; git --version; } 2>&1 | tee -a "$LOG/transcript.txt"
   claude plugin list 2>&1 | tee -a "$LOG/transcript.txt"
   claude plugin marketplace list 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected: `No plugins installed.` and one marketplace, `anthropic-plugin-directory` (built in). If you see your real plugins, `CLAUDE_CONFIG_DIR` was not picked up: repeat step 2 in this same terminal.

## Part 2: install as the README says

The README gives two slash commands for inside a Claude Code session. The command-line forms below do the same thing and need no login, so run them first; they are the verified path.

4. Add the marketplace:
   ```
   claude --debug-file "$LOG/04-marketplace-add.log" plugin marketplace add kmutahar/pmo-docs 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected, in order: `Adding marketplace…`, `Cloning via SSH: ...` (the SSH address of the repo on GitHub), `Clone complete, validating marketplace…`, `✔ Successfully added marketplace: pmo-docs`.

   Note: the short form `kmutahar/pmo-docs` clones over **SSH**. A reader with no GitHub SSH key may fail here with a permission or host-key error. If so, give the full HTTPS address instead, and report that the README should say so:
   ```
   claude plugin marketplace add https://github.com/kmutahar/pmo-docs.git 2>&1 | tee -a "$LOG/transcript.txt"
   ```

5. Install the plugin. Project scope keeps it inside the scratch folder:
   ```
   claude --debug-file "$LOG/05-install.log" plugin install pmo-docs@pmo-docs --scope project 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected: `✔ Successfully installed plugin: pmo-docs@pmo-docs (scope: project)`. The README does not give a scope; without `--scope` the default is user scope. The project scope writes a small `.claude/settings.json` (`enabledPlugins`) into the scratch project.

6. Confirm it:
   ```
   claude plugin list 2>&1 | tee -a "$LOG/transcript.txt"
   claude plugin list --json 2>&1 | tee -a "$LOG/transcript.txt"
   claude plugin details pmo-docs 2>&1 | tee -a "$LOG/transcript.txt"
   cat "$TRY/project/.claude/settings.json" 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected: `pmo-docs@pmo-docs`, `Scope: project`, `Status: ✔ enabled`; the version reads `0.0.0` until the first release, then it must equal the version in `.claude-plugin/plugin.json`. `details` shows `Skills (1)  pmo-docs`, no agents, hooks or MCP servers, and about 160 tokens always on, about 3.2k when the skill is used.

7. In a Claude Code session the same two steps are the slash commands from the README. Optional, needs a login (Part 3, step 11):
   ```
   /plugin marketplace add kmutahar/pmo-docs
   /plugin install pmo-docs@pmo-docs
   ```

## Part 3: does the skill work from the install?

8. Find the installed copy and list it:
   ```
   SKILLDIR="$CLAUDE_CONFIG_DIR/plugins/cache/pmo-docs/pmo-docs/0.0.0/skills/pmo-docs"
   ls "$SKILLDIR" "$SKILLDIR/scripts" 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected: `SKILL.md`, `assets`, `references`, `scripts`; scripts `setup.py`, `render_views.py`, `where.py`, `structure_check.py`, `docs_audit.py`, `overdue.py`, `pmo_common.py` and `_vendor`.
   (The folder name `0.0.0` is the installed version; change it after a release.)

9. Run the scripts from the install, with the system Python and nothing installed with pip. This is the check that the vendored PyYAML works:
   ```
   python3 "$SKILLDIR/scripts/setup.py" --name Demo --manager "Pat Example" 2>&1 | tee -a "$LOG/transcript.txt"
   ls "$TRY/project/pmo" 2>&1 | tee -a "$LOG/transcript.txt"
   python3 "$SKILLDIR/scripts/render_views.py" 2>&1 | tee -a "$LOG/transcript.txt"
   python3 "$SKILLDIR/scripts/render_views.py" --check 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected: `created: pmo/...` lines, then `registers valid; wrote 16 views to pmo/views`, and `--check` exits 0. An `ImportError` for `yaml` is a release blocker.

10. Update path (the README mentions it). Nothing newer exists before a release:
    ```
    claude --debug-file "$LOG/10-update.log" plugin update pmo-docs@pmo-docs --scope project 2>&1 | tee -a "$LOG/transcript.txt"
    ```
    Expected: `✔ pmo-docs is already at the latest version (0.0.0).`

11. **Live session (not yet run; needs a login).** A fresh home has no login, so this uses your account and a little usage. Start Claude Code in the scratch project and sign in with `/login` if asked:
    ```
    cd "$TRY/project" && rm -rf pmo     # start from an empty project again
    claude --debug-file "$LOG/11-session.log"
    ```
    Ask: `set up a project office`. Expected:
    - The `pmo-docs` skill fires.
    - It asks for the project name, manager and priority order, shows the files it will create, and **waits for your yes**.
    - Before you say yes, check from another terminal that nothing was written: `ls "$TRY/project"` shows no `pmo/` folder.

12. Answer with a fake name (project `Demo`, manager `Pat Example`) and say yes. Expected: a `pmo/` folder appears with `config.yaml`, `registers/`, `documents/`, `views/`.

13. Ask: `add a task: set up staging, high priority, due 2026-03-10`, then `render the views`. Expected: `pmo/registers/tasks.yaml` holds the task and `pmo/views/tasks.md` shows it. Leave the session with `/exit`.

## Part 4: clean up and share

14. Remove the plugin and the marketplace (the folder removal does it anyway):
    ```
    claude plugin uninstall pmo-docs@pmo-docs --scope project 2>&1 | tee -a "$LOG/transcript.txt"
    claude plugin marketplace remove pmo-docs 2>&1 | tee -a "$LOG/transcript.txt"
    claude plugin list 2>&1 | tee -a "$LOG/transcript.txt"
    ```
    Expected: `✔ Successfully uninstalled plugin`, `✔ Successfully removed marketplace`, `No plugins installed.`

15. Look through `$LOG/transcript.txt` once before sharing. The logs contain your machine's temp paths and your GitHub address, nothing secret, but read them anyway.

16. Make one file to share:
    ```
    tar -czf ~/pmo-install-check-logs.tgz -C "$TRY" logs
    ls -l ~/pmo-install-check-logs.tgz
    ```

17. Delete the throwaway folder and unset the variables:
    ```
    cd ~
    rm -rf "$TRY"
    unset TRY LOG CLAUDE_CONFIG_DIR SKILLDIR
    ```
    Check that your real setup is untouched: in a normal terminal `claude plugin list` shows your usual plugins.

## What the 2026-11-05 run found

- Add, install, details, scripts from the install, update, uninstall: all pass. `CLAUDE_CONFIG_DIR` does isolate the install.
- Live session: the skill loaded (`Loaded 1 skills from plugin pmo-docs`), asked its questions and wrote nothing before the yes, then `setup.py` ran from the installed copy. Adding a task flagged that a 2026-03-10 due date is already past and left owner, team, group and period as `null` instead of guessing. The debug log holds only three harmless errors (Datadog flush, a lock held by another process, a terminal escape code).
- Version is `0.0.0` until the first release.
- The short form `kmutahar/pmo-docs` clones over SSH. Strangers without an SSH key may need the HTTPS address (step 4). Decision for the maintainer: say so in the README, or leave it.
- The installed plugin folder holds the **whole repo** (`dev/`, `tests/`, `evals/`, `docs/`, root `CLAUDE.md`), because the marketplace entry has `"source": "./"`. Only `skills/pmo-docs/` is the skill. It is harmless (nothing there is on a PATH, `dev/` has no `bin/`), but `AGENTS.md` says `dev/` is "not shipped", which is not true for the install cache. Decision for the maintainer: leave it, or move the plugin into a subfolder later.
- The README gives no `--scope`; the default is user scope.

## If a step fails

| Symptom | Likely cause | Fix in the repo |
|---|---|---|
| Step 4: repo not found, permission denied or host key error | no GitHub SSH key, or the repo is not public | use the HTTPS address; README |
| Step 4: manifest invalid | `marketplace.json` wrong | `.claude-plugin/marketplace.json`, run `claude plugin validate .` |
| Step 5: plugin not found in marketplace | name mismatch between marketplace and plugin | the `name` fields in both manifests |
| Step 6: no skill in `details` | `skills/pmo-docs/SKILL.md` front matter invalid | `claude plugin validate .` |
| Step 9: `ImportError` for `yaml` | vendored PyYAML path broken | `skills/pmo-docs/scripts/_vendor/` |
| Step 11: the skill does not fire | `description` does not match the request, or a restart is missing | `SKILL.md` description |
| Step 11: files written before your yes | a real behaviour bug | `SKILL.md` rule 3, then re-run the `setup-needs-consent` eval |

Then send `~/pmo-install-check-logs.tgz` (or paste the failing step's output) to the agent, which fixes the README, the manifests or the skill and records the result in `memory.md` and `docs/PLAN.md`.

Not covered here: other agents (copying `skills/pmo-docs/` into their skills folder), Windows, and macOS. Those stay "untested" in the README.
