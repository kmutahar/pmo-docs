---
playbook_version: 1
---

Reads: pmo/config.yaml (registers, vocab), `roster.yaml`, the register being changed, the export the user names.

# Intake

The rules on consent, credentials, origin and definition of done live in `SKILL.md` (Safety rules, Working rules); this playbook gives the steps to turn a chat export into reviewed register entries.

## Steps

1. **Get the input**
   A path the user names, or pasted text. Any format (plain text, JSON, HTML, a messenger export): read it yourself, in parts when it is long; do not write a parser or run a script on it. Never copy the export into the project.

2. **Credentials**
   Do not copy, quote or use anything that looks like a password, token, key or a link with a password. Count such lines and say so in the reply, without quoting; tell the user to remove them from the chat and change them if they were shared. The registers reject them anyway (`render_views.py`).

3. **Extract candidates**
   New tasks, finished work, decisions, risks, issues and actions. For each: the register, a title in the user's words, the owner (map the sender to a roster slug; an unknown sender leaves `owner` empty and goes to the open questions; never add a person to the roster from a chat), a date (the message date for finished work; a due date only when a message states one), the evidence as message date and sender (not the message text).

4. **Compare with the registers**
   `grep` titles. A match is shown as "already tracked as T-n", never added twice. A chat message never changes the status of an existing entry (`SKILL.md`, Status from evidence): show it as a proposal.

5. **Show the proposal**
   One table: register, proposed id, title, owner, status, date, evidence, and `origin: proposed` for all rows. Count rows. More than about ten: show the list first and apply it after a yes (`SKILL.md`, Ids and bulk edits). Finished work is shown with `status: done`, the date it was finished in `done_on` and `period` the month of that date; `due` stays empty unless a message states a deadline. Ask once for the batch: was this work tested (QA passed), or may it be recorded with the note `no test evidence recorded` (`SKILL.md`, Definition of done)? Wait for the answer.

6. **Write what was confirmed**
   Only the confirmed rows, one line each, new ids as the highest number for the prefix plus one, `origin: stated` for confirmed rows, `notes` saying `from chat export, intake <YYYY-MM-DD>`; add `no test evidence recorded` where the user agreed to it. Fields the user did not confirm stay empty.

7. **Validate**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_views.py`; fix what it reports. A credential error means a line was copied by mistake: remove it.

8. **Stale documents**
   Run `python3 ${CLAUDE_SKILL_DIR}/scripts/docs_audit.py`; name the finished documents it reports as stale and offer to redraft them (`references/draft.md`). Redraft nothing unasked.

9. **Reply**
   Counts (proposed, written, already tracked, skipped), credential lines found (a count), open questions, the one next step.

## Do not

- Write anything before the user confirmed the rows.
- Quote chat text.
- Copy the export into the project.
- Store phone numbers, emails or credentials from a chat.
- Change an existing entry's status from a chat.
- Add people to the roster.
- Mark work done without the QA answer.
