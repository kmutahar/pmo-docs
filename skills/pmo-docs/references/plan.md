Reads: pmo/config.yaml (doc_types), `where.py` output, and the registers named in the doc type's `generated_from`.

# Plan

Where each planning document gets its content and what to ask. Producing the document is `references/draft.md`; this playbook adds the inputs and checks that are specific to planning. Rules for empty values, filling templates and planning (capacity, dates, dependencies, scope changes) are in `SKILL.md`.

## Steps

1. **Pick the document**
   Use the table below. Ask which one if the request is only "a plan".

2. **Check the inputs**
   Read the registers in the table. Note what is missing. Ask the user only for what is in the "Ask only if missing" column; anything else missing is written as `not set` or `not provided`.

3. **Apply the planning rules** in `SKILL.md` while you draft.

4. **Draft**
   Follow `references/draft.md` from step 2.

5. **Reply**
   Add to the usual reply: the registers read, and which of their entries are still `origin: proposed`.

## Where the content comes from

| Document | Content comes from | Ask only if missing |
|---|---|---|
| project-charter | `objectives`, `priorities` (goals), `budget`, `assumptions`, `roster` | purpose, in and out of scope, who approves |
| project-plan | `tasks`, `milestones`, `priorities` (goals), `teams`, `risks`, `assumptions`, `dependencies`, `changes`, `roster` | the objective of the period |
| roadmap | `milestones`, `priorities` (goals), `dependencies`; Now is the current period | what is Next and Later, target months |
| weekly-plan | `tasks` (in progress, due this week, carried over), `actions`, `capacity`; pass `--week` to `where.py` | leave this week, any priority change |
| capacity-plan | `capacity`, open tasks per owner, `roster` | working days and leave per person |
| team-checklist | `tasks`, `teams`, `milestones` | nothing |

## Do not

- Fill budget amounts or approvals the registers or the user have not given.
- Edit registers while drafting, unless the user gave new facts (then `references/track.md` first).
