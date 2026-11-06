# After 1.0: documents with several writers

Status: planned (light packages). Decided with the maintainer on 2026-11-06 (UTC). Hub and settled decisions: [`docs/PLAN.md`](../PLAN.md).

v0.1 to 1.0 are built for one writer per project and are safe for teams: duplicate ids fail validation, `renumber.py` fixes them (1.0), views are deterministic, and the launcher makes a shared hook possible (v0.5). What is left is documents that two people edit.

## Scope

**In**

- **An editor per draft.** A draft may carry `editor: <roster slug>` in its front matter. The current writer is named in `pmo/.me`, one roster slug, untracked (setup adds `pmo/.gitignore` with `.me`). Before editing a draft whose `editor` is someone else, the agent says so and asks. No locks.
- **Merge rules, written down.** Registers: one-line entries merge cleanly; a duplicate id is fixed with `renumber.py`. Views: render again. Drafts: a conflict is resolved by hand, then `structure_check`. Finished documents: never merged; a second finished version is a new draft.

**Out**

- Locks, a server, or any network check.

## Decisions (settled 2026-11-06)

| # | Topic | Decision |
|---|---|---|
| D1 | Draft ownership | `editor:` front matter field plus untracked `pmo/.me`. A warning and a question, never a block. |
| D2 | Schema version | Stays 1: `editor` is optional and only in documents. |

## Packages

| Package | Size | Model | Commit subject |
|---|---|---|---|
| W1 Editor field: `pmo/.me` in setup, `editor` written by draft, the warning in `SKILL.md` and `draft.md`, a `structure_check` test that `editor` is allowed and stripped or kept at Finish (decide in the package; default: kept) | S | Sonnet high | `feat: name the editor of a draft` |
| W2 Merge rules: one section in `references/git.md` and the README | S | Haiku low | `docs: how merges work with several writers` |
| W3 Release | S | maintainer + Sonnet | `chore(release): vX.Y.0` |

## Open questions

- Is a warning enough, or do teams want `docs_audit` to list drafts edited by someone other than their `editor`? Decide when a team asks.
