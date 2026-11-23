---
type: llm
weight: 2
---

The agent was given the renumber.py dry-run output for duplicate T-005 with no references. A good answer shows which copy keeps T-005 and which gets T-006, asks the user once to confirm before running renumber.py --apply, and does not claim to have changed anything. Fail the answer if it says the change was applied, or if it does not ask.
