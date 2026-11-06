---
name: publish
description: Publish finished pmo-docs documents to the configured folder or docs repo. Runs only when the user types /pmo-docs:publish.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/publish.py *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/docs_audit.py *) Bash(git -C * status *) Bash(git -C * diff *)
---

# publish

Follow `${CLAUDE_PLUGIN_ROOT}/references/publish.md` step by step. Before reading that playbook, check if `<paths.playbooks>/publish.md` (default `pmo/playbooks/publish.md`) exists; if it exists, read that file instead. In that playbook and in
`${CLAUDE_PLUGIN_ROOT}/SKILL.md`, read `${CLAUDE_SKILL_DIR}` as `${CLAUDE_PLUGIN_ROOT}`: the scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`. The rules in `${CLAUDE_PLUGIN_ROOT}/SKILL.md` apply; read its Safety rules first.
This command, typed by the user, is the ask for publishing, but the `repo`-mode commit still needs its own yes.
