Reads: pmo/config.yaml (paths, doc_types), `where.py` output, the audit scripts' output, and the documents and registers a check compares.

# Recipe: docs-audit

Run as `docs-audit [--fix]` (`--fix` is a recipe flag, not a script flag: `docs_audit.py` does not take it); the scope is every document unless the user names a folder. Produces a draft `docs-audit-report` for the current month. Draft only. The scripts check what a script can; you check the rest by reading.

## Steps

1. **Find the path**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/where.py docs-audit-report`.

2. **Run the mechanical checks**
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py --check`: register validity and stale views.
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py`: front matter, stale, old and broken links.
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/structure_check.py`: documents against their templates.
   Each exits 1 on findings. A non-zero exit is a result to report, not a failure of the audit. The template comments a draft keeps are expected: report every other error.

3. **Do the checks by reading**
   - Document against register: a checklist's ticks against `tasks` statuses, and a plan's goals, owners and dependencies against the registers. List the differences both ways.
   - Drift against code: only when the user names the folders that hold the code and the documents that describe it. Compare what the document claims with what the code does, read-only, and report only clear contradictions with a file and line on both sides. Without folders, list the check under Not checked.

4. **Draft the report**
   Fill the template (`references/draft.md` steps 4 to 8): one summary row per check with its count (0 is a valid count), findings with severity (high is wrong or contradicts the code, medium is stale or missing, low is naming or front matter), evidence as a file and line or the command, and a suggested fix. Anything not run goes under Not checked.

5. **Fixes (only with `--fix`)**
   Fix only drafts under `paths.documents`: missing front matter keys and draft file names. Show the planned changes first and wait for a yes. List every change under Fixes applied. Otherwise write "None (no fixes requested)". A stale finished document is listed and a redraft is offered, never done.

6. **Reply**
   Totals by severity, the three most important findings, and which playbook fixes each (`track`, `draft`, `month-start`).

## Do not

- Edit anything outside `paths.documents`, or any document the user edited by hand.
- Finish, publish, send or commit.
