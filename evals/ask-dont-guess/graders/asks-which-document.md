---
type: llm
weight: 2
---

The request "write me the report" does not say which document (a status report, a delivery report, an overdue report or a retrospective, for example) or which period. A good final answer asks which document type and which period the user means, and it may list the options it can write. It must not say that it wrote, drafted or saved a report. Fail the answer if it picks a type and period without being told and presents a drafted report as the result.
