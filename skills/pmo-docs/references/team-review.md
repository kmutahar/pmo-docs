---
playbook_version: 1
---

Reads: pmo/config.yaml, `team_review.py` output, registers `tasks`, `risks`, `issues`, `actions`, `requirements`, `roster`, and each translation language's glossary file.

# Recipe: team-review

Run as `team-review [--csv]`. Produces, for each roster person, a checklist of the open entries they own that need their check, as Markdown (default) or CSV. It is not a document type: it writes nothing unless the user asks.

## Steps

1. **Validate**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check`. Stop on register errors.

2. **Collect**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/team_review.py`, with `--csv` when the user asked for CSV. Its output is the result: do not recount, reorder or add entries by hand.
   It lists open tasks, risks, issues, actions and requirements per owner. Glossary rows under Proposed of each translation language are listed for the project manager, who moves them to Approved. Entries with no owner, or an owner not on the roster, have their own heading.

3. **Reply**
   Show the output. Say how many entries have no owner and, if any, recommend assigning them with the user (`references/track.md`). Save it to a file only when the user names a path inside the project and says yes.

## Do not

- Change a status, an owner or a glossary row.
- Send the checklists to anyone, finish, publish or commit.
