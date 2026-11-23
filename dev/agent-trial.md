# Trial the skill in other agents

A maintainer checklist, not shipped. Record results in your `tmp/` notes (section 5) and update the README's agent table at release. You run each agent yourself, in its own terminal session, and save what it did. The commands below are for zsh and write to `~/pmo-trial-logs/`.

Each trial works on a copy of the example project, `examples/acme`, in `~/pmo-trial/`, and installs the skill temporarily in `~/.agents/skills/pmo-docs` until cleanup. Nothing here touches your real projects' files, though your agents will see the trial skill until you remove it in cleanup.

Set these once per terminal, from the root of your clone:

```
export CLONE=<path to your clone>
export AGENT=<codex|gemini|cursor|copilot>
export SKILL=~/.agents/skills/pmo-docs
export LOG=~/pmo-trial-logs/$(date -u +%Y%m%dT%H%MZ)-$AGENT
mkdir -p "$LOG" ~/pmo-trial
```

## 1. Install per agent

All four agents read the shared folder `~/.agents/skills`, so one temporary copy serves them all. Extract a clean copy from git into a temp folder first (so no `__pycache__` or untracked files come along), remove any prior trial copy, then install it:

```
rm -rf ~/.agents/skills/pmo-docs ~/pmo-trial/skill-tmp
mkdir -p ~/.agents/skills ~/pmo-trial/skill-tmp
git -C "$CLONE" archive --prefix=pmo-docs/ HEAD:skills/pmo-docs | tar -x -C ~/pmo-trial/skill-tmp
cp -R ~/pmo-trial/skill-tmp/pmo-docs ~/.agents/skills/ 2>&1 | tee -a "$LOG/install.txt"
rm -rf ~/pmo-trial/skill-tmp
ls "$SKILL/SKILL.md" "$SKILL/scripts" 2>&1 | tee -a "$LOG/install.txt"
```

The folders each agent searches:

| Agent | User folders | Project folders | Source |
|---|---|---|---|
| Codex | `~/.agents/skills` | `.agents/skills` in the working folder, parent folders and repo root | developers.openai.com/codex/skills (redirects to learn.chatgpt.com/docs/build-skills) |
| Gemini CLI | `~/.gemini/skills`, `~/.agents/skills` | `.gemini/skills`, `.agents/skills` | geminicli.com/docs/cli/skills |
| Cursor | `~/.agents/skills`, `~/.cursor/skills` | `.agents/skills`, `.cursor/skills` | cursor.com/docs/skills |
| Copilot | `~/.copilot/skills`, `~/.agents/skills` | `.github/skills`, `.claude/skills`, `.agents/skills` | docs.github.com, Copilot CLI "add skills" |

Each agent needs a restart or a new session after the copy. Then ask it to list its skills. `pmo-docs` should appear with its description.

Per agent, check these lines in the log:

- **Codex:** no install step beyond the copy. Start Codex in the copy of Acme (section 3) and check that it names `pmo-docs`.
- **Gemini CLI:** the skill folders are an experimental feature. If `/skills list` shows nothing, turn on Agent Skills in its settings. The setting's exact name is unconfirmed; record what you did.
- **Cursor:** the skill shows in the agent's skill list after a restart. Cursor also reads `.claude/skills` and `.codex/skills`, so a copy there is found too; record which copy it used.
- **Copilot:** the copy in `~/.agents/skills` is the one to test. Copilot CLI and VS Code agent mode both read `.github/skills`; do not add one unless the trial needs it.

Record the result of this section in `$LOG/install.txt`: the list the agent printed, and the copy it used.

## 2. The install prompt

In a fresh session, give each agent the exact prompt from [`README.md`](../README.md#let-an-agent-install-it) (replacing the tag only if testing an unreleased commit).

The prompt must end with the agent asking before any write. Answer yes only to the install step, and record each question the agent asked in `$LOG/install.txt`.

## 3. The five prompts on a temp copy of Acme

Make a fresh copy for the four project prompts. The setup prompt needs an empty folder:

```
rm -rf ~/pmo-trial/acme ~/pmo-trial/setup
cp -R "$CLONE/examples/acme" ~/pmo-trial/acme
mkdir -p ~/pmo-trial/setup
```

Run the five prompts in order, in the same session, on the folder named in the table. After prompt 1 (`setup` in an empty folder), list the created files; before prompt 2 (`track` in `~/pmo-trial/acme`), take a baseline hash snapshot, then after each prompt (`P=track`, `render`, `draft`, `finish`) save the agent's transcript to `$LOG/$P-transcript.txt` and diff the hashes:

```
# After prompt 1 (setup):
cd ~/pmo-trial/setup
find pmo -type f | sort | tee "$LOG/setup-files.txt"

# Before prompt 2 (baseline for prompts 2 to 5):
cd ~/pmo-trial/acme
find pmo -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$LOG/acme-prev.sha"

# After each prompt in ~/pmo-trial/acme (set P=track|render|draft|finish):
cd ~/pmo-trial/acme
find pmo -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$LOG/acme-after-$P.sha"
diff -u "$LOG/acme-prev.sha" "$LOG/acme-after-$P.sha" | tee -a "$LOG/acme-changed-$P.txt"
cp "$LOG/acme-after-$P.sha" "$LOG/acme-prev.sha"
```

The expected files come from `docs/walkthrough.md` and the scripts. To build the reference copy once, copy `examples/acme` to `~/pmo-trial/reference` (`rm -rf ~/pmo-trial/reference && cp -R "$CLONE/examples/acme" ~/pmo-trial/reference`) and run prompts 2 to 5 in Claude Code on it (plus prompt 1 in `~/pmo-trial/reference-setup` if you want a setup reference). Compare each agent's result with that reference:

| # | Prompt | Folder | Expected file changes | Pass when |
|---|---|---|---|---|
| 1 | setup | `~/pmo-trial/setup` | `pmo/config.yaml`, `pmo/house-rules.md`, `pmo/documents/.gitkeep`, the starter registers under `pmo/registers/`, `pmo/views/` (one view per register plus the catalogue), `pmo/bin/pmo` | Files match the reference. The agent asked for the project name and manager, and did not overwrite anything. |
| 2 | track | `acme` | Two turns. Turn 1 ("mark T-001 done"): asks for QA evidence and changes nothing. Turn 2 (give the evidence): only the `T-001` line in `pmo/registers/tasks.yaml` changes (`status: done`, `done_on` set); `pmo/views/tasks.md` is re-rendered. | No change before the evidence. Then only that line and that view change. |
| 3 | render | `acme` | Hand-edit one status in `tasks.yaml`, then ask for a re-render. Only `pmo/views/tasks.md` changes. | `render_views.py --check` exits 0 after the prompt. No view was edited by hand. |
| 4 | draft | `acme` | One new draft under `pmo/documents/`, at the path `where.py status-report --week` gives. The 2026-03 report is untouched. No register changes. | `structure_check.py` passes on the new file. Its status is `draft`. |
| 5 | finish | `acme` | Only `pmo/documents/2026-03 - Status report.md`: `status` becomes `finished`, the template version and hashes are recorded, template comments are removed. Acme configures `ar` under `languages`, so Finish asks once whether to translate into `ar` (answer `no`). | `structure_check.py` passes. The new draft from prompt 4 is still a draft. |

The prompt texts for the agent:

- Setup: `Set up pmo-docs for this project. The project is Acme Portal, the manager is Sam Example.`
- Track: `Mark T-001 done.` Then, after it asks: `The QA evidence is the staging checklist, signed off on 2026-03-15.`
- Render: `I changed a status by hand in tasks.yaml. Check the registers and re-render the views.`
- Draft: `Draft this week's status report.`
- Finish: `Finish the 2026-03 status report.`

Run `where.py` to see the draft path for prompt 4 and the template for prompt 5. Do not give the agent the path; the skill should find it:

```
python3 "$SKILL/scripts/where.py" status-report --week --hashes 2>&1 | tee -a "$LOG/where-draft.txt"
```

Compare the result with the reference copy:

```
diff -r ~/pmo-trial/reference/pmo ~/pmo-trial/acme/pmo 2>&1 | tee -a "$LOG/diff-vs-claude-code.txt"
python3 "$SKILL/scripts/render_views.py" --check --project ~/pmo-trial/acme 2>&1 | tee -a "$LOG/check.txt"
python3 "$SKILL/scripts/structure_check.py" --project ~/pmo-trial/acme 2>&1 | tee -a "$LOG/structure.txt"
```

Some files differ by date or by draft name. Note those, but a difference is a fail only when a rule in `SKILL.md` is broken or a file the prompt should not touch changed.

Also check the safety rules: no commit, no push, no password or token copied from the chat, no register edited without the evidence in prompt 2. Record any break in section 4.

Clean up only after the logs are safe (if you are stopping here and skipping section 4, also remove `~/.agents/skills/pmo-docs`):

```
rm -rf ~/pmo-trial/acme ~/pmo-trial/setup
```

## 4. The switch trial

Agent A sets up the project and edits it. Agent B then takes the install prompt (section 2) on the same project, and must write nothing to the project. Pass when B writes nothing and its render leaves the views unchanged.

1. Prepare `~/pmo-trial/switch` (copy Acme there first):

```
rm -rf ~/pmo-trial/switch && cp -R "$CLONE/examples/acme" ~/pmo-trial/switch
```

2. Agent A: run prompts 2 to 3 in `~/pmo-trial/switch` (and prompt 1 in a fresh folder if you want to test setup too). Then take a snapshot:

```
cd ~/pmo-trial/switch
find pmo -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$LOG/before.sha"
```

3. Agent B: start a new session of the other agent in `~/pmo-trial/switch` and give it the install prompt from section 2. Tell it the project is already set up and that nothing in `pmo/` may change. Save its transcript to `$LOG/switch-B-transcript.txt`.

4. Compare:

```
cd ~/pmo-trial/switch
find pmo -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$LOG/after.sha"
diff "$LOG/before.sha" "$LOG/after.sha" 2>&1 | tee -a "$LOG/switch-diff.txt"
python3 "$SKILL/scripts/render_views.py" --check --project ~/pmo-trial/switch 2>&1 | tee -a "$LOG/switch-check.txt"
```

Pass when `switch-diff.txt` is empty, the check exits 0, and B's transcript shows the verify step and no write under `pmo/`. A copy written to `~/.agents/skills` by B is allowed only when B asked for a yes first (the install prompt requires it).

Clean up after the logs are safe:

```
rm -rf ~/pmo-trial/switch ~/.agents/skills/pmo-docs
```

## 5. Fill the results table

Add one row per agent to your notes (a file in `tmp/`). Use the UTC date in the Notes column. Each cell is one short word or a pass/fail:

- **Version:** the `metadata.version` the agent's copy reports (from `SKILL.md`).
- **Skill found:** `yes` when the agent listed `pmo-docs` without a manual path.
- **Scripts ran:** `direct`, `launcher`, or `none`.
- **setup, track, render, draft, finish:** `pass` or `fail`.
- **Notes:** the date, the switch-trial result (`switch pass` or `switch fail`), and any failure line.

Record a failure as one line in the Notes cell, with this form:

```
YYYY-MM-DD UTC | <prompt> | <what happened, in one sentence> | likely file: <path in the skill or the project>
```

Example: `2026-11-12 UTC | track | agent wrote the views by hand | likely file: skills/pmo-docs/references/track.md`.

If an agent cannot load skill folders at all, say so in the table and stop there, and tell the maintainer.

Save the agent's final message for each prompt in `$LOG`. The table needs only the counts and the one-line notes, but the logs are what you share if a result is disputed.
