# Check the walkthrough in a throwaway session

A maintainer checklist, not shipped to users. Run it before each release. It does three things in a throwaway Claude Code home, with the plugin installed from your clone:
- runs every command of [`docs/walkthrough.md`](../docs/walkthrough.md);
- checks that the outputs still match the page;
- runs the agent prompts in a live session.

None of your own plugins, hooks or settings are loaded. Everything goes to `$LOG` in `~/pmo-release-logs/`, which no block deletes:
- `transcript.txt`: setup and install
- `scripts.txt`: walkthrough sections 1 to 6
- `session.log`: debug log of the live session
- `*.jsonl`: the session transcript
- `agent-diff.txt`: file changes made by the agent

Share the `$LOG` folder. Use one terminal throughout, zsh or bash. Step 4 needs a login and uses a little usage.

**Keep in step:** when `docs/walkthrough.md` changes a command, an output or an agent prompt, change section 3 or 4 here in the same commit. When a version adds behaviour the agent should show, add a prompt to section 4.

## 1. Setup (from the root of your clone)

```sh
export REPO=$(git rev-parse --show-toplevel) TRY=$(mktemp -d -t pmo-walk-XXXXXX) LOG=~/pmo-release-logs/walkthrough-$(date -u +%Y%m%dT%H%M%SZ)
export CLAUDE_CONFIG_DIR="$TRY/claude-home"; mkdir -p "$LOG" "$CLAUDE_CONFIG_DIR"
for d in "$TRY/acme" "$TRY/scripts-acme" "$LOG/acme-before"; do cp -r "$REPO/examples/acme" "$d"; done
{ date -u; claude --version; python3 --version; git -C "$REPO" log --oneline -1; echo "TRY=$TRY LOG=$LOG"; claude plugin list; } 2>&1 | tee -a "$LOG/transcript.txt"
```
Expect: `No plugins installed.` If your own plugins show, `CLAUDE_CONFIG_DIR` was not picked up.

## 2. Install the plugin from the clone

```sh
cd "$TRY/acme"
claude --debug-file "$LOG/install.log" plugin marketplace add "$REPO" 2>&1 | tee -a "$LOG/transcript.txt"
claude --debug-file "$LOG/install.log" plugin install pmo-docs@pmo-docs --scope project 2>&1 | tee -a "$LOG/transcript.txt"
claude plugin details pmo-docs 2>&1 | tee -a "$LOG/transcript.txt"
export SKILL=$(ls -d "$CLAUDE_CONFIG_DIR"/plugins/cache/pmo-docs/pmo-docs/*/ | head -1); echo "SKILL=$SKILL" | tee -a "$LOG/transcript.txt"
```
Expect: `Successfully installed plugin: pmo-docs@pmo-docs (scope: project)`, and `SKILL` is a folder in the throwaway home. The folder name is the last released version until `dev/release` writes the new one.

## 3. Walkthrough sections 1 to 6 (scripts only, no model)

```sh
cd "$TRY/scripts-acme"; run() { echo "\$ $*"; "$@" 2>&1; echo "[exit $?]"; echo; }
T=pmo/registers/tasks.yaml; R="pmo/documents/2026-03 - Status report.md"
{
echo "## 1"; run python3 "$SKILL/scripts/render_views.py" --check
echo "## 2"; sed -i 's/\(id: T-2,.*\)status: not-started/\1status: done/' $T; run python3 "$SKILL/scripts/render_views.py" --check
run python3 "$SKILL/scripts/render_views.py"; run python3 "$SKILL/scripts/render_views.py" --check
sed -i 's/\(id: T-2,.*\)status: done/\1status: bogus/' $T; run python3 "$SKILL/scripts/render_views.py" --check
sed -i 's/\(id: T-2,.*\)status: bogus/\1status: not-started/' $T; run python3 "$SKILL/scripts/render_views.py"
echo "## 3"; run python3 "$SKILL/scripts/overdue.py" --as-of 2026-03-15
echo "## 4"; run python3 "$SKILL/scripts/where.py" status-report 2026-03 --hashes
echo "## 5"; run python3 "$SKILL/scripts/structure_check.py"
sed -i 's/^## Summary$/## Overview/' "$R"; run python3 "$SKILL/scripts/structure_check.py" "$R"; sed -i 's/^## Overview$/## Summary/' "$R"
run python3 "$SKILL/scripts/docs_audit.py" --as-of 2026-03-15
echo "## 6"; printf '\nlanguages:\n  translations: [xx]\n  xx: { label: XX, dir: rtl, glossary: pmo/data/glossary-xx.md }\n' >> pmo/config.yaml
run python3 "$SKILL/scripts/render_views.py" --check
run python3 "$SKILL/scripts/where.py" decision-log --lang xx --hashes
run python3 "$SKILL/scripts/where.py" docs-audit-report --lang xx
run python3 "$SKILL/scripts/parity_check.py"
run python3 "$SKILL/scripts/docs_audit.py" --as-of 2026-03-15
} 2>&1 | tee "$LOG/scripts.txt"
```
Expect: the same output as the walkthrough page, section by section. The `template` paths differ. `sed -i` here is GNU sed; on macOS use `sed -i ''`.

## 4. Live session

```sh
cd "$TRY/acme" && claude --debug-file "$LOG/session.log"
```
Sign in with `/login` if asked. Type these one at a time and read each answer before the next.

1. `Treat 2026-03-15 as today. mark T-1 done`
   Expect: the skill fires and asks for QA or test evidence. No file changes.
2. `QA passed, it was tested on staging`
   Expect: only the T-1 line changes, to `status: done` and `done_on: 2026-03-15`. The views are rendered with `render_views.py`, never edited by hand.
3. `weekly-status for the week of 2026-03-09`
   Expect: a new draft weekly status, with numbers from the registers.
4. `! printf '\nlanguages:\n  translations: [xx]\n  xx: { label: XX, dir: rtl }\n' >> pmo/config.yaml`
   (The `!` runs it as a shell command.) Then: `finish the 2026-03 status report`
   Expect:
   - the Finish steps run, ending with `status: finished` and `source_hashes`;
   - it asks once whether to translate into XX. Answer `no`.
5. `! mkdir -p inbox && printf '[2026-03-14 09:10] Sam Example: Bob, please add the footer links, due 2026-03-27\n[2026-03-14 11:30] Bob Example: the staging backup job is finished\n[2026-03-14 11:41] Alice Example: staging box password=Example-Pa55-zz\n' > inbox/chat.txt`
   Then: `take the new work and the finished work from inbox/chat.txt into the registers`
   Expect:
   - a table of proposed entries, and nothing written yet;
   - it asks whether the finished work was tested;
   - it mentions a credential line without quoting it.

   Answer `stop, write nothing`.
6. `/exit`

## 5. Save the result

```sh
cp -r "$TRY/acme" "$LOG/acme-after"; diff -ru -x .claude "$LOG/acme-before" "$LOG/acme-after" > "$LOG/agent-diff.txt"
cp "$CLAUDE_CONFIG_DIR"/projects/*/*.jsonl "$LOG/"; ls -la "$LOG" | tee -a "$LOG/transcript.txt"
```

Afterwards, these must pass on the final copy:
- `render_views.py --check` on `$LOG/acme-after`;
- `docs_audit.py --as-of 2026-03-15`.

The weekly draft keeps its template comments, so `structure_check.py` reports it, as it does any draft. Record the result in the version's plan.

## 6. Cleanup (after you have checked `$LOG`; this also removes the throwaway login)

```sh
rm -rf "$TRY"; unset CLAUDE_CONFIG_DIR
```
