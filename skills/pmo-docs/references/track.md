---
playbook_version: 1
---

Reads: pmo/config.yaml (registers, vocab), the register being changed, `roster.yaml`.

# Track

Add, change or close entries in the registers. Rules on status, consent and proposed entries are in `SKILL.md` (Safety rules, Working rules); formats and ids are in `references/conventions.md`. Use only the fields the register lists in the config.

## Steps

1. **Pick the register and the operation**
   Match the request to a row of the table below. If it names no register, or fits two, ask.

2. **Find the entry**
   For an existing entry search the register file for `id: T-14[,}]` (the search tool, or `grep -nE 'id: T-14[,}]' <register file>`). A register without ids is found by its keys (`grep -n 'slug: alice' ...`, or `person` and `period` for capacity). Read that one line.

3. **Check for a scope change**
   Moving a date, owner or priority of committed work, or adding or dropping a goal, is a scope change: go to `references/govern.md` (change request) first, unless the user says it is the agreed new plan. Then apply it and log a `DEC-` entry (`references/govern.md`).

4. **Edit one line**
   Edit that line only (new entries go at the end of the list). Before the first entry of `requirements`, `tests`, `environments` or `permissions`, copy its starter file from `${CLAUDE_SKILL_DIR}/assets/starter/optional-registers/` to `paths.registers/`. A new id is the highest number for the prefix plus one. Check that an owner is in the roster and that every value is in the vocabulary. Ask for a missing owner, date or priority; leave it `null` until answered.

5. **Validate**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py` and fix what it reports before going on. When validation reports a duplicate id, run `renumber.py`. Show the dry run's keeps and gets lines and ask the user once whether the right copy keeps the id: the choice is by file order, and people may have used the id where the script cannot see. With references, match each reference to a copy by its title, owner and context and put that in the same question. After the yes, run `--apply` (with the flags, if there are references).

6. **List stale documents**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py`. Name the finished documents the audit reports as stale and the drafts it reports as behind. Offer to redraft or refresh them (`references/draft.md`). Redraft nothing unasked.

7. **Reply**
   List the entries changed as id, field, old value, new value. Then the stale documents and the one next step.

## Operations

| User says | You do |
|---|---|
| "T-14 is done", "in progress", "blocked", "dropped" | Set `status` on that line. `done` follows the definition of done in `SKILL.md` (with a `tests` register in use, see `SKILL.md`, Definition of done), which also says when to set `done_on` (for `done` and `dropped`). The test link and the "no test evidence recorded" note follow `SKILL.md`, Definition of done. For `blocked`, put the reason in `notes` and ask who can unblock it. Evidence from git or a checklist only suggests a change: say what it is and wait for a yes. |
| "add a task" | New `T-` entry with `status: not-started`. Ask for any of title, team, group, priority, owner, period and due that is missing. |
| "add a requirement, test, environment, permission" | New `REQ-`, `TST-`, `ENV-` or `PERM-` entry. Before the first entry of an optional register, copy its starter file (step 4). |
| "add a goal, milestone, objective, budget item" | New `P-` (goal), `M-`, `O-` or `B-` entry. A new goal, or a date or owner change on an existing milestone, is a scope change (step 3). A task's priority is a level, not a goal (`SKILL.md`, Working rules). |
| "add a team", "change a team's owners" | One `TM-` entry per team in `teams`: `order`, `heading`, `owners`. Owners are roster slugs. |
| "add capacity", "leave for alice" | One entry per person and period in `capacity`; no id. Unknown days stay `null`. |
| "add a person", "change a role" | One entry per person in the roster: `slug`, `name`, `role`. A slug in use is never renamed. |
| "we have a risk, issue, assumption, dependency" | New `R-`, `I-`, `A-` or `D-` entry. Risks need probability, impact, owner and mitigation; issues need severity and owner. Set `raised` to the date given. |
| "close R-2", "resolve I-1" | Set the status and the register's closing date (`closed` for risks, `resolved` for issues). Keep the entry, never delete it. |
| "action: alice does X by DATE" | New `ACT-` entry with owner and due. Ask if either is missing. |
| "we decided ...", "we had a meeting ..." | `references/govern.md` (decision log, meeting minutes). |
| a pasted message or list with tasks | See "Pasted lists" below. |

## Pasted lists

A chat export or a long conversation goes to `references/intake.md`. For a short paste:

1. Read the text and list every task, risk, action or decision it contains.
2. Show a table first: one row per proposed entry (register, title, owner, due, what the text said), with `origin: proposed` on every row you inferred. Write nothing yet.
3. Write only the rows the user confirms: `origin: stated` for what they confirmed as fact, `origin: proposed` for a row they want kept as unconfirmed.

## Do not

- Break a rule in `SKILL.md`: Working rules "Ids and bulk edits", "Status from evidence".
- Put long text in a register; it belongs in a document, referenced by id.
