---
playbook_version: 1
---

Reads: pmo/config.yaml (publish, doc_types), `publish.py` output, `docs_audit.py` output.

# Recipe: publish

Run as `/pmo-docs:publish`. Copies finished documents to the configured folder or git repository.

## Steps

1. **Check configuration**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/publish.py` (no `--apply`).
   If the publish mode is `none`, explain the two modes (`folder` and `repo`) and the config lines needed in `pmo/config.yaml`, then stop.

2. **Review candidates**
   Show the listing grouped by state:
   - For each `conflict`, show the diff of target vs source (`git diff` or compare both files) and ask, per file, whether to overwrite.
   - For each `stale`, explain which registers changed since the document was finished (run `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py`) and ask whether to publish anyway (`--include`) or redraft first.

3. **Confirm the copy**
   Show the final list of files to copy and wait for the user's explicit yes.

4. **Apply changes**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/publish.py --apply` with the agreed `--overwrite <REL>` and `--include <REL>` flags. Report what was copied and what was left uncopied.

5. **Folder mode**
   If `publish.mode` is `folder`, tell the user the files are in place and that they commit them when ready (`references/git.md`). Stop.

6. **Repo mode**
   If `publish.mode` is `repo`:
   Run `git -C <path> status --short` and show the output. If it lists staged entries outside the copied files, name them: they stay out of the commit.
   Ask: "Commit these N files in <path>? (no push)".
   Only on a clear yes:
   Stage each copied file individually: `git -C <path> add -- <each copied target path>` (one path per argument, never `-A` or `.`).
   Commit: `git -C <path> commit -m "docs: publish <N> documents (<period or date>)" -- <each copied target path>` (the path list keeps work the user staged earlier out of the commit).
   Never push; show the user the command to push when they choose.
   Mention any pre-existing changes in that repository and leave them untouched.

7. **Reply**
   Summarise what was copied, what was skipped and why, commit status, and links when `url` is configured.

## Limits

The Safety rules in `${CLAUDE_SKILL_DIR}/SKILL.md` apply: rule 1 for the `repo`-mode commit, rule 3 for overwrites. Only finished documents are copied, the source documents are never changed, and `--apply` runs only after the user agrees to the list.
