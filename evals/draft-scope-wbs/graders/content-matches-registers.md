---
type: llm
weight: 2
focus: {source: file, path: pmo/documents/Scope and work breakdown.md}
---

The scope and work breakdown draft (`pmo/documents/Scope and work breakdown.md`) is a draft for "Acme Portal" (as of 2026-03-15) that matches the Acme registers:

- Front matter has `type: scope-wbs` and `status: draft`.
- The Work breakdown table has one row per deliverable (grouping by goal is fine). Every task `T-001` through `T-004` and requirement `REQ-001` appears in the Tasks and requirements column of some row. The Owner cell is a roster name or `not set`. The Milestone cell reads `not set` or `not recorded`, because tasks carry no milestone link.
- Goals (`GL-001`, `GL-002`), assumptions (`A-001`, `A-002`), `REQ-002`, the milestones (`M-001`, `M-002`) and the objectives (`O-001`, `O-002`) may appear (for example in In scope, Assumptions or Open questions), but are not required. No other id appears, and no title, owner or date contradicts the registers. Out of scope may read `None` or `not recorded`.
- A missing person or date reads `not set`, `not provided` or `not recorded`; otherwise the person comes from a register or the roster and the date from a register.
