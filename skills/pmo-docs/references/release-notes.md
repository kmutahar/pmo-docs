---
playbook_version: 1
---

Reads: pmo/config.yaml (doc_types.release-notes), pmo/house-rules.md, `where.py` output, registers `tasks`, `changes`; git commit log.

# Recipe: release-notes

Run as `release-notes [--repo PATH] [--since REF] [--until REF] [--period YYYY-MM]`. Produces a draft `release-notes` for one period. Draft only.

## Steps

1. **Find the repository and paths**
   `--repo` defaults to the project folder; with `--repo`, every git command below runs as `git -C <repo> ...` (read-only). The document is written into this project's `paths.documents`. With `--repo`, the document title is `Release notes - <repo folder name>`, passed as `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py release-notes <period> --title "Release notes - <folder>"`, so multiple repos in one month do not collide.
   Period defaults to the month of `--until`'s commit date (or the current month).

2. **Find the range**
   Start with `--since` if given. Otherwise, look for `covers_to` in the newest finished or draft `release-notes` document in `paths.documents` with the same title (the same repo). If none exists, find the first commit of the period's month: run `git log --reverse --since=<YYYY-MM-01> --format=%H` (in `allowed-tools`; no pipes) and take the first line. The range begins at that commit's parent; with no parent (the repo's first commit), use that commit itself and say so.
   `--until` defaults to `HEAD`.
   Resolve both boundaries with `git rev-parse` to full SHAs for front matter (`covers_from` and `covers_to`).

3. **Read the commit log**
   Run `git log --no-merges --format='%H%x09%s' <from>..<to>` (read-only; `references/git.md`).

4. **Sort and rewrite commits**
   Categorise each commit by its subject:
   - `feat` → New
   - `fix` → Fixed
   - `!` after the type or `BREAKING CHANGE` in subject → Breaking changes (only there)
   - `chore`, `ci`, `test`, `build`, `style`, `refactor`, `docs` → Internal
   - Anything else, including non-conventional subjects → Improved
   Rewrite each commit line for an external reader (short, concrete sentence). Keep the 7-character abbreviated SHA in backticks: `(`sha7`)`.

5. **Link tasks**
   If the commit subject explicitly names a task id (using the prefix from `registers.tasks.prefix` in `pmo/config.yaml`), link it on the line: `- <change> (`<sha7>`) - <id>`.
   Any keyword or title match without an explicit id in the message is shown only as a proposed link under Open questions, not written into the notes (`SKILL.md` Safety rule 2).

6. **Identify documentation updates**
   List any existing project documents whose subject the changes touch, each marked "proposed" under Docs to update with the reason.

7. **Draft the document**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py release-notes <period> [--title "..."]`. If the file exists, follow `references/draft.md` step 2. Fill the template with `covers_from`, `covers_to`, and the categorised sections. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py "<file>"`.

8. **Reply**
   Report the document path, counts per section, proposed task links, and the next step: review, edit, then Finish (`references/finish.md`).

## Do not

- Change task statuses from commits (`SKILL.md`, Status from evidence).
- Break the Safety rules in `SKILL.md`: finishing, publishing, sending or committing are not part of this recipe.
