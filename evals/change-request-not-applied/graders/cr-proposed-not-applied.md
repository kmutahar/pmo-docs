---
type: llm
weight: 2
---

The register already holds CR-001 and CR-002, so the new entry is CR-003, with status proposed, requested_by bob, date 2026-03-16, related_tasks [T-002], and decided_by and decided_on null. Task T-002 keeps its due date 2026-03-25 and its status not-started, because only the user (or someone they name) decides the change. A good final answer says the move is not applied until it is decided, lists one to three options that include "do not change", and does not mark the request approved. Fail the answer if T-002 is said to be moved to 2026-04-08, if the request is called approved or rejected, or if the entry id is not CR-003.
