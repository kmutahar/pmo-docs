---
playbook_version: 1
---

Reads: pmo/config.yaml (domain, technical, doc_types), the stack file for each stack, the registers named in the doc type's generated_from, the code the user names or the repository.

# Draft a technical document

Draft a technical document from the codebase and registers. Applies to `entity-lifecycle`, `api-reference`, `integration-guide`, `architecture-overview` and `user-guide`. For every other doc type, see `references/draft.md`. Rules for filling a template are in `SKILL.md`.

## Steps

1. **Identify the document**
   Confirm the doc type and period (`references/draft.md` steps 1 and 2). Stop and ask when needed config is missing: `domain.lifecycle_entity` for `entity-lifecycle`, `technical.consumers` for `integration-guide` (ask for consumer names; offer to set in config only after a yes), or `domain.roles` for `user-guide` and `entity-lifecycle`.

2. **Pick the stack**
   Read `technical.stacks`. If empty, read `Detected by:` across project and skill `stacks/` files, compare with the repository, and propose a match to confirm with the user. If none matches, ask the user once. After a yes, write `pmo/playbooks/stacks/<stack>.md` from official docs with headings: `Routes, pages or screens`, `Data models`, `Permissions and auth`, `Config and environments`, `Tests`, `List the API live`. Offer to set `technical.stacks`. Open each project stack file if present, else the skill default.

3. **Inventory**
   Use the stack file "Look in" lines to find routes, pages, screens, models, auth rules, config and tests. If the project has a code-graph or index tool, use it for this step. Otherwise Glob, grep and Read. Keep a short summary table (kind, count, folders) for the reply; do not write it to a file.

4. **Read the code**
   Open each item at file and line, read it and note facts. Cite `path:line` in the document. Skip generated files, vendored code and lockfiles (rules: `SKILL.md`, Documents).

5. **Fan out**
   When the inventory exceeds ~15 files, split by folder into slices. Run sub-agents if available (at most three at once), returning lines `item | path:line | fact` without code or secrets. Otherwise work through slices in order. Merge findings; conflicting facts go to Open questions.

6. **Record findings**
   Show facts that belong in registers (new roles not in `domain.roles`, environments, permissions, requirements) as proposals first; after a yes write them with `origin: proposed` (`references/track.md`). Record role and variable names (`SKILL.md`, Documents). Note a secret by file and line only (`SKILL.md`, No credentials).

7. **Fill the template**
   Follow `references/draft.md` steps 4 and 6. Set `code_ref` to `git rev-parse HEAD` output (`not set` without git). Every item carries `path:line`. Unseen details become `not recorded` in Open questions. Without user-provided output write "read from the code, not run".

8. **Live listing**
   Offer the stack file "List the API live" command. The user runs it, or approves the agent running it (`SKILL.md`, Documents). If output is provided, compare against code readings and list differences.

9. **Check and reply**
   Run structure check (`references/draft.md` step 8). Reply with the document path, inventory counts per kind, items not found, register proposals awaiting approval, and next steps.

## Do not

- Break the code-read rules in `SKILL.md`, Documents.
- Edit the code.
- Finish the document.
