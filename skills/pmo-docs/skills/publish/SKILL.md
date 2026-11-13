---
name: publish
description: Publish finished pmo-docs documents to the configured folder or docs repo. Runs only when the user types /pmo-docs:publish.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/publish.py) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/docs_audit.py *) Bash(git -C * status *) Bash(git -C * diff *)
---

# publish

Follow `${CLAUDE_PLUGIN_ROOT}/references/publish.md` step by step. Before reading that playbook, check if `<paths.playbooks>/publish.md` (default `pmo/playbooks/publish.md`) exists; if it exists, read that file instead. In that playbook and in the main SKILL.md the scripts folder is written with the variable named CLAUDE_SKILL_DIR (dollar sign and braces). For this command the scripts folder is `${CLAUDE_PLUGIN_ROOT}/scripts/`. The rules in `${CLAUDE_PLUGIN_ROOT}/SKILL.md` apply; read its Safety rules first.
This command, typed by the user, is the ask for publishing, but the `repo`-mode commit still needs its own yes. Run the dry run first and show the listing; the user typing this command is the ask, so run `--apply` after you show the listing and the user answers yes (Claude Code asks for permission to run it).
