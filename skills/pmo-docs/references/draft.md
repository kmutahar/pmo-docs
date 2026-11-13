---
playbook_version: 1
---

Reads: pmo/config.yaml (doc_types), pmo/house-rules.md, `where.py` output, the doc type's template, the registers named in its `generated_from`.

# Draft

Write one draft of one document from its template and the registers. Rules for filling a template are in `SKILL.md` (Documents, Working rules, Empty values).

## Steps

1. **Identify the document**
   A request to translate a document goes to `references/translate.md`. A generator writes English only (`references/conventions.md`). Take the doc type from `doc_types` in the config; ask if it is unclear. Take the period from the request. With none, use the current month (a weekly document, such as `weekly-plan`, uses the current week: pass `--week`). A type named by `{date}` needs the date of the event: ask. For an existing draft whose `editor` is someone else, see `SKILL.md` (Documents, Editor).

2. **Find the paths**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py <type> [period] [--week] [--as-of YYYY-MM-DD]`. Note the document path, the template path, `template_version` and `generated_from`.
   - Document exists and is a draft: do not overwrite. If its `editor` is someone else, follow the Editor rule in `SKILL.md` (Documents). Ask whether to continue editing it or to refresh its register-derived parts. A refresh keeps the hand-written text and shows what changed.
   - Document exists and is finished: say so. If the user wants a new draft, set it back to `status: draft` and drop `source_hashes`, then continue as for a draft.

3. **Check the registers**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check`. Stop on validation errors and report them. If only the views differ from the registers, say so, offer to render them, and carry on.

4. **Read the template**
   Read the whole template, including its comments and `checks:`. The comments say how to fill each section; the checks say what will be verified.

5. **Gather the content**
   - For documents written from code (`entity-lifecycle`, `api-reference`, `integration-guide`, `architecture-overview`, `user-guide`), follow `references/draft-technical.md` to gather content from the codebase and stack files.
   - Read the registers named in `generated_from`. A document is a view of them.
   - Run `python3 ${CLAUDE_SKILL_DIR}/scripts/overdue.py` when the template lists overdue work.
   - Use git history only as read-only evidence (`references/git.md`).
   - A fact in no source: ask, or write `not set`, `not provided` or `not recorded` as `SKILL.md` says, and list it as an open question. If a register lacks something the template needs, offer to add it (`references/track.md`); never fill it from an older document.

6. **Fill the template**
   If the doc type has `generator: true`, run `python3 ${CLAUDE_SKILL_DIR}/scripts/generate.py <type> [period] [--week] [--as-of DATE]` and fill only what it left (prose placeholders, `{{comment}}`-style cells, the agent sections). Put its `note:` lines in Open questions. If the document already exists, `generate.py` exits 3 and writes nothing: run it with `--stdout`, show the user the differences from the existing file, and replace only the generated sections after a yes. Never delete the file to regenerate it (`SKILL.md` Safety rule 3). Otherwise fill every section as the Documents rules in `SKILL.md` say. Keep the comments in place; Finish removes them.


7. **Write the file**
   Write the document to the path `where.py` printed, creating the folder if needed. A new draft gets `editor: <slug>` from `pmo/.me` in its front matter (`SKILL.md`, Documents, Editor). A draft of a type with `generated_from` gets the `source_hashes:` line from `where.py <type> [period] --hashes` in its front matter (a generator writes it). A request to draft is consent to write that one file.

8. **Check**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py "<file>"`. The comments you kept are reported as errors: ignore those and nothing else. Fix every other error and run it again.
   Compare counts: every task, goal or entry the template promises appears once, and numbers in the prose equal the rows in the tables.

9. **Reply**
   Give the path, a summary of three to six lines, the open questions (at most five), and the next step: edit it, then say it is ready to finish.

## Do not

- Finish the document.
- Edit registers, unless the user gave new facts (then follow `references/track.md` first).
- Fill test results, sign-offs or approvals; leave them for the people who give them.
