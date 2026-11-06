---
name: init
description: Set up a pmo-docs project office in the current folder. Runs only when the user types /pmo-docs:init.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_views.py *)
---

# init

Follow `${CLAUDE_PLUGIN_ROOT}/references/setup.md` step by step. Before reading that playbook, check if `pmo/playbooks/setup.md` exists; if it exists, read that file instead. In that playbook and in
`${CLAUDE_PLUGIN_ROOT}/SKILL.md`, read `${CLAUDE_SKILL_DIR}` as `${CLAUDE_PLUGIN_ROOT}`: the scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`. The rules in `${CLAUDE_PLUGIN_ROOT}/SKILL.md` apply; read its Safety rules first.

Arguments, if any: $ARGUMENTS (a project name the user already gave).
