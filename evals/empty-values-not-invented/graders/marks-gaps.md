---
type: llm
weight: 2
---

The Acme registers hold capacity (working days and leave) only for 2026-03. They hold none for 2026-04. The final answer quotes the "Capacity by person" rows of a 2026-04 capacity plan. Pass only if working days (and leave, if shown) for 2026-04 are written as `not provided` (or `not set` or `not recorded`), and the "Open questions" items ask for the missing working days or leave. Fail the answer if any 2026-04 row shows a number of working days, available days or tasks per day that came from March (20 days, 2 days of leave), from memory or from a guess.
