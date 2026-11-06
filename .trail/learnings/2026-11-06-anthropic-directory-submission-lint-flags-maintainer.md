---
title: Anthropic directory submission lint flags
author: maintainer
date: 2026-11-06
branch: main
cost: { minutes: 9, tokens: 161417 }
touches:
  - skills/pmo-docs/.claude-plugin/plugin.json
  - skills/pmo-docs/references/plan.md
  - PRIVACY.md
  - TERMS.md
---

## Decided
- The directory flagged MCP_FORWARDS_CREDENTIAL_ENV, RUNTIME_FETCH_EXEC, ASSETS_PASSED_UNREAD and ALLOWED_TOOLS_ENTRY_NOT_PLAIN (2026-11-06). All are false positives or notes.
- The "pass $$" credential match came from the word "pass" in `references/plan.md`; it now says "use `--week` with `where.py`".
- `plugin.json` has `displayName`, `documentationUrl`, `supportUrl`, `privacyPolicyUrl` and `termsOfServiceUrl`, and the repo has `PRIVACY.md` and `TERMS.md`. `tests/test_plugin.py` checks the fields and that both files exist.

## Tried and ruled out
- No network, curl, wget or credential reads in the skill's scripts (checked by grep). The "send data" half is a YAML tag URL in a comment in the vendored `parser.py`; vendored code is left alone.
- The download-and-run flag on `icon.png` is a byte-pattern coincidence in the image; no change needed.

## Watch out
- `${CLAUDE_SKILL_DIR}` in the `SKILL.md` `allowed-tools` is intended; the directory says it may stay.
