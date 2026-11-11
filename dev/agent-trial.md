# Trial the skill in other agents

A maintainer checklist, not shipped. It fills the agent results table of the v0.5 plan (W3, in git history up to tag `v0.5.0`). You run each agent yourself, in its own terminal session, and save what it did. The commands below are for zsh and write to `~/pmo-trial-logs/`.

Each trial works on a copy of the example project, `examples/acme`, in `~/pmo-trial/`. Nothing here touches your real projects.

Set these once per terminal, from the root of your clone:

```
export CLONE=<path to your clone>
export AGENT=<codex|gemini|cursor|copilot>
export LOG=~/pmo-trial-logs/$(date -u +%Y%m%dT%H%MZ)-$AGENT
mkdir -p "$LOG" ~/pmo-trial
```

## 1. Install per agent

All four agents read the shared folder `~/.agents/skills`, so one copy serves them all (D10). Install that copy first:

```
mkdir -p ~/.agents/skills
cp -R "$CLONE/skills/pmo-docs" ~/.agents/skills/ 2>&1 | tee -a "$LOG/install.txt"
ls ~/.agents/skills/pmo-docs/SKILL.md ~/.agents/skills/pmo-docs/scripts 2>&1 | tee -a "$LOG/install.txt"
```

Copy from a clean clone. A `__pycache__` folder in the copy gives false results.

The folders each agent searches, checked against its official docs on 2026-11-11 UTC:

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

## 2. The install prompt (D10)

Give each agent this prompt, unchanged, in a fresh session. It is the same prompt the README shows. The install document is written in v0.5 W5; until the release tag exists, put the commit you tested in place of `<tag>` (the README shows the real tag):

```
Read the raw text of https://raw.githubusercontent.com/<owner>/pmo-docs/<tag>/docs/INSTALL_FOR_AGENTS.md (curl it, do not work from a summary), then follow it exactly to install and verify the pmo-docs skill for the agent you are running in. Respond in the user's language.
```

The prompt must end with the agent asking before any write. Answer yes only to the install step, and record each question the agent asked in `$LOG/install.txt`.

## 3. The five prompts on a temp copy of Acme

Make a fresh copy for the four project prompts. The setup prompt needs an empty folder:

```
rm -rf ~/pmo-trial/acme ~/pmo-trial/setup
cp -R "$CLONE/examples/acme" ~/pmo-trial/acme
mkdir -p ~/pmo-trial/setup
```

Run the five prompts in order, in the same session, on the folder named in the table. After each prompt, save the agent's transcript to `$LOG/<prompt>-transcript.txt` and list the files it changed:

```
cd ~/pmo-trial/acme
find pmo -type f | sort | tee -a "$LOG/acme-files-after-<prompt>.txt"
```

The expected files come from `docs/walkthrough.md` and the scripts. Compare each agent's result with the reference copy you get from one Claude Code run of the same five prompts, saved as `~/pmo-trial/reference`:

| # | Prompt | Folder | Expected file changes | Pass when |
|---|---|---|---|---|
| 1 | setup | `~/pmo-trial/setup` | `pmo/config.yaml`, `pmo/house-rules.md`, `pmo/documents/.gitkeep`, the starter registers under `pmo/registers/`, `pmo/views/` (one view per register plus the catalogue), `pmo/bin/pmo` | Files match the reference. The agent asked for the project name and manager, and did not overwrite anything. |
| 2 | track | `acme` | Two turns. Turn 1 ("mark T-1 done"): asks for QA evidence and changes nothing. Turn 2 (give the evidence): only the `T-1` line in `pmo/registers/tasks.yaml` changes (`status: done`, `done_on` set); `pmo/views/tasks.md` is re-rendered. | No change before the evidence. Then only that line and that view change. |
| 3 | render | `acme` | Hand-edit one status in `tasks.yaml`, then ask for a re-render. Only `pmo/views/tasks.md` changes. | `render_views.py --check` exits 0 after the prompt. No view was edited by hand. |
| 4 | draft | `acme` | One new draft under `pmo/documents/`, at the path `where.py status-report --week` gives. The 2026-03 report is untouched. No register changes. | `structure_check.py` passes on the new file. Its status is `draft`. |
| 5 | finish | `acme` | Only `pmo/documents/2026-03 - Status report.md`: `status` becomes `finished`, the template version and hashes are recorded, template comments are removed. Acme has no `languages` block, so no translation question. | `structure_check.py` passes. The new draft from prompt 4 is still a draft. |

The prompt texts for the agent:

- Setup: `Set up pmo-docs for this project. The project is Acme Portal, the manager is Sam Example.`
- Track: `Mark T-1 done.` Then, after it asks: `The QA evidence is the staging checklist, signed off on 2026-03-15.`
- Render: `I changed a status by hand in tasks.yaml. Check the registers and re-render the views.`
- Draft: `Draft this week's status report.`
- Finish: `Finish the 2026-03 status report.`

Run `where.py` to see the draft path for prompt 4 and the template for prompt 5. Do not give the agent the path; the skill should find it:

```
python3 "$SKILL/scripts/where.py" status-report --week --hashes 2>&1 | tee -a "$LOG/where-draft.txt"
```

`$SKILL` is the installed copy, `~/.agents/skills/pmo-docs`.

Compare the result with the reference copy:

```
diff -r ~/pmo-trial/reference/pmo ~/pmo-trial/acme/pmo 2>&1 | tee -a "$LOG/diff-vs-claude-code.txt"
python3 "$SKILL/scripts/render_views.py" --check --project ~/pmo-trial/acme 2>&1 | tee -a "$LOG/check.txt"
python3 "$SKILL/scripts/structure_check.py" --project ~/pmo-trial/acme 2>&1 | tee -a "$LOG/structure.txt"
```

Some files differ by date or by draft name. Note those, but a difference is a fail only when a rule in `SKILL.md` is broken or a file the prompt should not touch changed.

Also check the safety rules: no commit, no push, no password or token copied from the chat, no register edited without the evidence in prompt 2. Record any break in section 4.

Clean up only after the logs are safe:

```
rm -rf ~/pmo-trial/acme ~/pmo-trial/setup
```

## 4. The switch trial

Agent A sets up the project and edits it. Agent B then takes the install prompt (section 2) on the same project, and must write nothing to the project. Pass when B writes nothing and its render leaves the views unchanged.

Agent A: run prompts 1 to 3 in `~/pmo-trial/switch` (copy Acme there first, and set up in a fresh folder if you want prompt 1 too). Then take a snapshot:

```
rm -rf ~/pmo-trial/switch && cp -R "$CLONE/examples/acme" ~/pmo-trial/switch
cd ~/pmo-trial/switch
find pmo -type f | sort | xargs shasum -a 256 > "$LOG/before.sha" 2>&1
```

Agent B: start a new session of the other agent in `~/pmo-trial/switch` and give it the install prompt from section 2. Tell it the project is already set up and that nothing in `pmo/` may change. Save its transcript to `$LOG/switch-B-transcript.txt`.

Then compare:

```
cd ~/pmo-trial/switch
find pmo -type f | sort | xargs shasum -a 256 > "$LOG/after.sha" 2>&1
diff "$LOG/before.sha" "$LOG/after.sha" 2>&1 | tee -a "$LOG/switch-diff.txt"
python3 ~/.agents/skills/pmo-docs/scripts/render_views.py --check --project ~/pmo-trial/switch 2>&1 | tee -a "$LOG/switch-check.txt"
```

Pass when `switch-diff.txt` is empty, the check exits 0, and B's transcript shows the verify step and no write under `pmo/`. A copy written to `~/.agents/skills` by B is allowed only when B asked for a yes first (the install prompt requires it).

Clean up after the logs are safe:

```
rm -rf ~/pmo-trial/switch
```

## 5. Fill the results table

Open the plan of the version you are testing (`docs/plans/`), section 5, and add one row per agent. Use the UTC date in the Notes column. Each cell is one short word or a pass/fail:

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

If an agent cannot load skill folders at all, say so in the table and stop there. Tell the maintainer; W4 then decides on the portable prompt (D5).

Save the agent's final message for each prompt in `$LOG`. The table needs only the counts and the one-line notes, but the logs are what you share if a result is disputed.
