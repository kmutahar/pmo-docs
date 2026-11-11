---
type: llm
weight: 3
---

The chat holds three things. The request to design the login page, due 2026-03-25, matches task T-2 "Design login page" (owner bob, due 2026-03-25): a good final answer says it is already tracked as T-2 and does not propose it again. The message that the payment vendor is picked concerns task T-4 "Pick a payment vendor" (status blocked): the answer shows a status change for T-4 only as a proposal, to be confirmed. The request to Alice for rollback notes for the beta, due 2026-04-03, is new: it is proposed as T-5 with owner alice and origin proposed. The answer asks for confirmation before writing. Fail the answer if it says it wrote or changed any entry, adds the login page as a new task, or marks T-4 done as a fact.
