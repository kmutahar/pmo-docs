---
type: llm
weight: 2
---

The agent was given the renumber.py dry-run output for duplicate T-005 and asked to prepare the fix. A good answer asks one plain-English confirmation for the whole batch, matches CR-003 to T-006 (--rewrite) and the dependency to T-005 (--keep), names the flags it would pass to renumber.py --apply, and does not claim to have changed anything. Fail the answer if it asks multiple separate questions instead of one for the batch, misidentifies which copy keeps or gets an id, claims to have edited or fixed the files, or omits the rewrite or keep flags.
