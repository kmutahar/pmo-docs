---
type: llm
weight: 3
---

The approved French glossary says "Decision log" is "Registre des décisions" and "Open questions" is "Points en suspens". A good final answer quotes a title line and a `#` heading that use "Registre des décisions" (for example "Registre des décisions - Acme Portal"), a last-section heading "Points en suspens", and the Summary row of DEC-1 with the id DEC-1 and the date 2026-02-12 unchanged (status and decision text may be in French). It says the original and the approved glossary were not changed, and that new terms went to the proposed glossary file. Fail the answer if the title or last heading uses another translation of those two terms, or if an id or date differs from the original.
