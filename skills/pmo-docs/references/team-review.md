---
playbook_version: 1
---

Reads: pmo/config.yaml, `assets/config.default.yaml`, `team_review.py` output, registers `tasks`, `risks`, `issues`, `actions`, `requirements`, `roster`, each translation language's glossary file and, with `--lang`, its names file.

# Recipe: team-review

Run as `team-review [--csv] [--lang CODE]`. Produces, for each roster person, a checklist of the open entries they own that need their check, as Markdown (default) or CSV, with each entry's description and question when it has them. It is not a document type: it writes nothing unless the user asks.

## Steps

1. **Validate**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check`. Stop on register errors. If the script cannot run, say the check was not run and carry on.

2. **Collect**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/team_review.py`, with `--csv` when the user asked for CSV and `--lang <code>` for a translation language's wording of each entry's description and question (the entry's own text where the names file has none). When the script runs, its output is the result: do not recount, reorder or add entries by hand. If it cannot run, do not stop: read the registers and each translation glossary directly, group the open tasks, risks, issues, actions and requirements by owner (roster order; an entry is open when its status is not in that register's `closed` list: read `registers.<name>.closed` from `pmo/config.yaml`, else from `${CLAUDE_SKILL_DIR}/assets/config.default.yaml`, so a requirement is closed only as `verified` or `dropped` and `accepted` is still open), list the glossary rows under Proposed for the project manager, give entries with no owner or an owner not on the roster their own heading, and say in the reply that the script was not run.
   It lists open tasks, risks, issues, actions and requirements per owner. Glossary rows under Proposed of each translation language are listed for the project manager, who moves them to Approved. Entries with no owner, or an owner not on the roster, have their own heading.

3. **Reply**
   Show the output. Say how many entries have no owner and, if any, recommend assigning them with the user (`references/track.md`). Save it to a file only when the user names a path inside the project and says yes.

## Import answers

Run as `team-review --import FILE.csv` after reviewers fill in the CSV from `--csv` (a `done` column: `x`, `yes`, `true` or `1` means done; an `answer` column: free text). Needs the `register` and `id` columns.

1. **Preview**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/team_review.py --import FILE.csv`. It writes nothing. It lists, with counts, the status changes (current status -> the register's done status: first of `registers.<name>.done`, else of `closed`), answers with no status change, ids already at the proposed status, unknown ids, rows it skipped (such as glossary rows) and rows with no answer.
2. **Confirm**
   Show the proposed changes to the user and ask one plain yes/no for the whole batch. Mention the unknown ids and skipped rows. Do not edit anything before the yes.
3. **Apply**
   After the yes, edit each entry with a targeted edit as `SKILL.md` Working rules say (status, and `done_on`/`resolved`/`closed` dates where the register has them; record an answer in the entry's `notes` or the field the user names), then run `render_views.py`. After a no, change nothing.

## Do not

- Change a status, an owner or a glossary row, except as Import answers describes after a yes.
- Send the checklists to anyone, finish, publish or commit.
