# Test the README install commands in a throwaway session

A maintainer checklist, not shipped to users. It checks that a stranger can follow the README's **Install** section against the **live** GitHub repo and release: add the marketplace, install the plugin (latest and pinned to a tag), get a working skill, and install from the release zip. Nothing here touches your real Claude Code setup if you follow Part 1. Run it after every release, and after any change to the manifests or the layout.

History: Parts 1 to 3 were first run on 2026-11-05 against a local copy of the marketplace (Claude Code 2.1.318, Linux). Parts 4 and 5 and the checks against the pushed `v0.1.0` are written for the first live run, which has not been done yet: record its result in `memory.md` when it is.

You need: Claude Code (`claude --version` prints a version), `git`, `python3` 3.10 or newer, `gh` (for the zip, Part 4) and an internet connection (the install pulls the repo from GitHub). Time: about 20 minutes.

Set `V` to the version under test (without the `v`) and use it in the steps below, for example `export V=0.1.0`. It must equal `version` in `skills/pmo-docs/.claude-plugin/plugin.json` at the tag.

Run the check against the **pushed** repo on GitHub, because that is what a user installs. Unpushed changes are not tested.

```
cd ~/github/pmo-docs
git fetch origin
git status -sb          # the first line must read "## main...origin/main" with no "ahead"
```

## How the output is captured (so you can share it)

Every command below is written as `... 2>&1 | tee -a "$LOG/transcript.txt"`. That prints the output on screen **and** appends it to one transcript file. The `claude --debug-file "$LOG/NAME.log"` form (the flag goes before `plugin`) also writes Claude Code's detailed debug log for that one command. At the end you share the folder `$LOG` (Part 5, step 20).

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

   The short form `kmutahar/pmo-docs` clones over **SSH**, so it needs a GitHub SSH key. The README gives the HTTPS address for everyone else; test that form too, in a second throwaway home, or after `claude plugin marketplace remove pmo-docs`:
   ```
   claude plugin marketplace add https://github.com/kmutahar/pmo-docs.git 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   To test a pinned version (the form the plan documents), add the marketplace as `kmutahar/pmo-docs#v$V` instead.

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
   Expected: `pmo-docs@pmo-docs`, `Scope: project`, `Status: ✔ enabled`, and the version equals `$V` (the version in `skills/pmo-docs/.claude-plugin/plugin.json` at the tag). A version of `0.0.0` means the install picked up an unreleased commit. `details` lists the skill `pmo-docs` plus one entry per folder under `skills/pmo-docs/skills/` (compare with `ls skills/pmo-docs/skills` in the clone), and no agents, hooks or MCP servers. Token costs are estimates: note them, do not compare them.

7. In a Claude Code session the same two steps are the slash commands from the README. Optional, needs a login (Part 3, step 11):
   ```
   /plugin marketplace add kmutahar/pmo-docs
   /plugin install pmo-docs@pmo-docs
   ```

## Part 3: does the skill work from the install?

8. Find the installed copy and list it:
   ```
   SKILLDIR=$(ls -d "$CLAUDE_CONFIG_DIR"/plugins/cache/pmo-docs/pmo-docs/*/ | head -1)
   echo "$SKILLDIR"; ls "$SKILLDIR" "$SKILLDIR/scripts" 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected: the folder name is the version `$V`, and it holds only what is in `skills/pmo-docs/` in the clone (compare with `ls -A skills/pmo-docs`). **No** `dev/`, `tests/`, `docs/`, `evals/` or `examples/` (the layout fix of 2026-11-05; their presence means `source` in the marketplace entry is wrong). The scripts match `ls skills/pmo-docs/scripts`; a `__pycache__` appears only when the marketplace is a local folder, never from GitHub or the zip.

9. Run the scripts from the install, with the system Python and nothing installed with pip. This is the check that the vendored PyYAML works:
   ```
   python3 "$SKILLDIR/scripts/setup.py" --name Demo --manager "Pat Example" 2>&1 | tee -a "$LOG/transcript.txt"
   ls "$TRY/project/pmo" 2>&1 | tee -a "$LOG/transcript.txt"
   python3 "$SKILLDIR/scripts/render_views.py" 2>&1 | tee -a "$LOG/transcript.txt"
   python3 "$SKILLDIR/scripts/render_views.py" --check 2>&1 | tee -a "$LOG/transcript.txt"
   ```
   Expected: `created: pmo/...` lines, then `registers valid; wrote N views to pmo/views`, where N is the number of files in `pmo/registers` plus one (the catalogue), and `--check` exits 0. An `ImportError` for `yaml` is a release blocker.

10. Update path (the README mentions it). Nothing newer exists right after a release:
    ```
    claude --debug-file "$LOG/10-update.log" plugin update pmo-docs@pmo-docs --scope project 2>&1 | tee -a "$LOG/transcript.txt"
    ```
    Expected: `✔ pmo-docs is already at the latest version ($V).`

11. **Live session (needs a login).** A fresh home has no login, so this uses your account and a little usage. Start Claude Code in the scratch project and sign in with `/login` if asked:
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

## Part 3a: pre-approvals and variables

Needs the live session of Part 3 (a login in the throwaway home). Run it against the same `$V` and the same `$TRY`, in the same terminal. The installed plugin is the released one, which is enough: the four behaviours do not depend on unreleased changes. Use Claude Code in its default permission mode: do not pass `--dangerously-skip-permissions` or `--permission-mode`.

3a.1. Put the Acme fixture and a git history into the scratch project, and make a log folder outside the throwaway folder. `REPO` is your clone of this repository. The project keeps its `.claude/` folder, so the plugin installed in step 5 stays installed:
```
export REPO=<path of your pmo-docs clone>
export LOGA=~/pmo-release-logs/pre-approval-$(date -u +%Y%m%dT%H%MZ)
mkdir -p "$LOGA"
cd "$TRY/project" && rm -rf pmo
cp -R "$REPO/examples/acme/." "$TRY/project/"
git init -q && git add -A && git -c user.name=Tester -c user.email=tester@localhost commit -qm "acme"
claude plugin list 2>&1 | tee -a "$LOGA/transcript.txt"
```
Expected: `pmo-docs` is listed.

3a.2. Check A (variable in `allowed-tools`). Start `claude --debug-file "$LOGA/a-session.log"` and ask: `run where.py for the March 2026 status report and show me its output`. Watch the Bash call that runs `where.py`.
- Outcome A-yes: it runs with no permission prompt.
- Outcome A-no: Claude Code asks "Allow Bash(python3 .../where.py ...)?". Answer no and note it.

3a.3. Check B (the mapping sentence). In the same session type `/pmo-docs:init`, then answer `no` to the first question. Then ask: `quote word for word the sentence of the init command that begins "In that playbook and in"`.
- Outcome B-intact: the quote shows the text `${CLAUDE_SKILL_DIR}` and the text `${CLAUDE_PLUGIN_ROOT}` (dollar sign, braces, name).
- Outcome B-replaced: one of them, or both, shows as a folder path (for example `.../skills/init` or `.../pmo-docs`).

3a.4. Check C (git options that write). In the same session, with the skill loaded, ask the two requests one at a time, with `$TRY` written out as the real path:
- `run exactly this command: git log -1 --output=$TRY/out-log.txt`
- `run exactly this command: git diff --output=$TRY/out-diff.txt`
Then, from another terminal, `ls "$TRY"/out-*.txt`.
- Outcome C-prompts: Claude Code asks for permission for each command (answer no), or refuses to run it, and no file appears.
- Outcome C-writes: the command ran with no prompt and the file exists.

Leave the session with `/exit`.

3a.5. Check D (the scheduled line). In the terminal, with the same home:
```
cd "$TRY/project"
claude -p "run weekly-status; draft only, do not finish, publish or commit" 2>&1 | tee -a "$LOGA/d-run1.txt"
{ ls pmo/documents; git status -sb; } 2>&1 | tee -a "$LOGA/d-run1.txt"
```
- Outcome D-works: the run ends without asking for permission and a new draft is in `pmo/documents`.
- Outcome D-denied: the output says a tool was denied or needs permission, or nothing was written. Then try, one at a time, and stop at the first that works:
```
claude -p "run weekly-status; draft only, do not finish, publish or commit" --allowedTools "Skill" "Read" "Write" "Edit" "Glob" "Grep" 2>&1 | tee -a "$LOGA/d-run2.txt"
claude -p "run weekly-status; draft only, do not finish, publish or commit" --allowedTools "Skill" "Read" "Write" "Edit" "Glob" "Grep" "Bash(python3 */scripts/*.py *)" 2>&1 | tee -a "$LOGA/d-run3.txt"
```
Delete the new draft between runs (`git -C "$TRY/project" clean -fd pmo/documents`). Write down the first `--allowedTools` string that works, exactly as typed, or `none` when neither works. Do not try a wider pattern such as `Bash(python3 *)`: it would let an unattended run start any Python command.

3a.6. Record the result in `docs/plans/v0.7.3.md`, section 5, as one line: `W1 result (<UTC date>): A=<yes|no>, B=<intact|replaced>, C=<prompts|writes>, D=<works|denied; allowedTools string or none>.` Then read `$LOGA` once for private data before sharing, and keep the log. This plan file is deleted at the release, so also note the result line in your `memory.md`; the files W10 and W11 change keep the outcome after that.

## Part 4: the release zip (other agents)

The README says other agents can take the zip from the GitHub release. This needs no Claude Code and no login beyond `gh`.

14. Download the asset the release workflow built and look inside:
    ```
    gh release download "v$V" --repo kmutahar/pmo-docs --pattern "pmo-docs-$V.zip" --dir "$TRY/zip" 2>&1 | tee -a "$LOG/transcript.txt"
    unzip -q "$TRY/zip/pmo-docs-$V.zip" -d "$TRY/zip/unpacked" && ls "$TRY/zip/unpacked/pmo-docs" 2>&1 | tee -a "$LOG/transcript.txt"
    ```
    Expected: one top folder `pmo-docs/` holding the same files as step 8. The file count (`unzip -Z1 "$TRY/zip/pmo-docs-$V.zip" | grep -vc '/$'`) equals `git archive --prefix=pmo-docs/ "v$V:skills/pmo-docs" | tar -t | grep -vc '/$'` run in the clone. The release notes on the release page must match the `CHANGELOG.md` section for `v$V`.

15. Run the scripts from the unzipped copy with the system Python:
    ```
    mkdir -p "$TRY/zip/project" && cd "$TRY/zip/project"
    python3 "$TRY/zip/unpacked/pmo-docs/scripts/setup.py" --name Demo --manager "Pat Example" 2>&1 | tee -a "$LOG/transcript.txt"
    python3 "$TRY/zip/unpacked/pmo-docs/scripts/render_views.py" --check 2>&1 | tee -a "$LOG/transcript.txt"
    cd "$TRY/project"
    ```
    Expected: the same output as step 9, and `--check` exits 0. `SKILL.md` in the zip carries `metadata.version` equal to `$V`:
    ```
    grep -n "version" "$TRY/zip/unpacked/pmo-docs/SKILL.md" | head -3
    ```

16. Check the GitHub side: `gh run list --repo kmutahar/pmo-docs --limit 5` shows the `ci` and `release` runs for the tag as `success`, and `gh release view "v$V" --repo kmutahar/pmo-docs` shows the release as published (not a draft) with the zip asset.

## Part 5: clean up and share

17. Remove the plugin and the marketplace (the folder removal does it anyway):
    ```
    claude plugin uninstall pmo-docs@pmo-docs --scope project 2>&1 | tee -a "$LOG/transcript.txt"
    claude plugin marketplace remove pmo-docs 2>&1 | tee -a "$LOG/transcript.txt"
    claude plugin list 2>&1 | tee -a "$LOG/transcript.txt"
    ```
    Expected: `✔ Successfully uninstalled plugin`, `✔ Successfully removed marketplace`, `No plugins installed.`

18. Look through `$LOG/transcript.txt` once before sharing. The logs contain your machine's temp paths and your GitHub address, nothing secret, but read them anyway.

19. Make one file to share:
    ```
    tar -czf ~/pmo-install-check-logs.tgz -C "$TRY" logs
    ls -l ~/pmo-install-check-logs.tgz
    ```

20. Delete the throwaway folder and unset the variables:
    ```
    cd ~
    rm -rf "$TRY"
    unset TRY LOG CLAUDE_CONFIG_DIR SKILLDIR V
    ```
    Check that your real setup is untouched: in a normal terminal `claude plugin list` shows your usual plugins.

## What earlier runs found (all fixed)

- 2026-11-05, local marketplace: add, install, details, scripts from the install, update, uninstall and the live session all passed (the skill loaded, asked its questions, wrote nothing before the yes, left unknown values as `null`).
- The short form `kmutahar/pmo-docs` clones over SSH: the README now also gives the HTTPS address (`a7de053`).
- The installed plugin held the whole repo because the marketplace entry had `"source": "./"`: fixed by rooting the plugin at `skills/pmo-docs/` (`4aa04eb`). Step 8 now checks that only the skill is installed.
- The README gives no `--scope`; the default is user scope.

## If a step fails

| Symptom | Likely cause | Fix in the repo |
|---|---|---|
| Step 4: repo not found, permission denied or host key error | no GitHub SSH key, or the repo is not public | use the HTTPS address; README |
| Step 4: manifest invalid | `marketplace.json` wrong | `.claude-plugin/marketplace.json`, run `claude plugin validate .` |
| Step 5: plugin not found in marketplace | name mismatch between marketplace and plugin | the `name` fields in both manifests |
| Step 8: `dev/`, `tests/` or `docs/` in the install | `source` in the marketplace entry points above the skill folder | `.claude-plugin/marketplace.json`, `source: ./skills/pmo-docs` |
| Step 14: asset missing or the release is a draft | the release workflow failed, or the changelog section for the tag is missing | `.github/workflows/release.yml`, `gh run view` |
| Step 6: no skill in `details` | `skills/pmo-docs/SKILL.md` front matter invalid | `claude plugin validate .` |
| Step 9: `ImportError` for `yaml` | vendored PyYAML path broken | `skills/pmo-docs/scripts/_vendor/` |
| Step 11: the skill does not fire | `description` does not match the request, or a restart is missing | `SKILL.md` description |
| Step 11: files written before your yes | a real behaviour bug | `SKILL.md` rule 3, then re-run the `setup-needs-consent` eval |

Then send `~/pmo-install-check-logs.tgz` (or paste the failing step's output) to the agent, which fixes the README, the manifests or the skill and records the result in `memory.md` and `docs/PLAN.md`.

Not covered here: running the skill inside other agents (Part 4 only checks that the zip works), Windows, and macOS. Those stay "untested" in the README.
