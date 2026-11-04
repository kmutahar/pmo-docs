Reads: pmo/config.yaml (registers, vocab), `changes`, `decisions`, `actions`, `meetings`, `where.py` output for the document being drafted.

# Govern

Change control, sign-off, definition of done, minutes, retrospectives and the decision log. Consent and status rules are in `SKILL.md`; register edits follow `references/track.md`; documents are drafted by `references/draft.md`.

## Change request

Trigger: anything that changes the scope, priority, owner or date of committed work.

1. **Record it**
   Add a `CR-` entry to `changes` with `status: proposed`, `title`, `requested_by`, `date`, `description`, `impact` and `related_tasks` (`references/track.md`).
2. **Draft it**
   Draft `change-request` (`where.py change-request --as-of <date>` gives the path). Fill the impact from the registers, offer one to three options including "do not change", and give a recommendation.
3. **Wait for the decision**
   The user, or the person they name, decides. Never mark a request approved or rejected yourself. When told the outcome: set `status`, `decided_by` and `decided_on`; add a `DEC-` entry; apply the change in the registers; then set the request to `implemented`.
4. **List stale documents**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py`, name the finished documents it reports as stale, and offer to redraft them.
   A rejected request stays in the register.

## Definition of done

Defined once in `SKILL.md` (Definition of done). When the user agrees to mark a task done without QA, record `no test evidence recorded` in its `notes`.

## Sign-off and acceptance

A goal's acceptance criteria are in `priorities` (`acceptance`, `accepted_by`, `accepted_on`; `SKILL.md`, Working rules). Fill the last two only with the name and date the user gives. A goal is `done` when its acceptance is signed off.

## Meeting minutes

1. Take the notes or transcript the user gives. Extract decisions, actions (owner and due) and open questions. Mark a missing owner or date and ask; never guess.
2. Register them: a `MTG-` entry, the `DEC-` entries and the `ACT-` entries (`references/track.md`). Link the minutes in `minutes_doc` once drafted.
3. Draft `meeting-minutes` (`references/draft.md`; `where.py meeting-minutes --as-of <meeting date>` gives the path). Every decision and action carries its id.

## Retrospective

1. Start from facts. Offer to draft `delivery-report` first.
2. Ask what went well, what did not and what was learned, unless the user has given it. Write it blameless.
3. Add each improvement as an `ACT-` entry with an owner and a due date, then draft `retrospective`.

## Decision log

Every decision is a `DEC-` entry with title, context, decision, `decided_by`, `date` and status. Add `options` and `consequences` when others must understand the decision later. Link a replaced decision with `supersedes`. The `decision-log` document is a view of `decisions`: after any decision change it is stale, so offer to redraft it (never unasked).

## Do not

- Approve, reject or sign anything on the user's behalf.
- Redraft a document the user edited by hand over their edits.
