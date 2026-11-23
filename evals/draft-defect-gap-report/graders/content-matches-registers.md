---
type: llm
weight: 2
focus: {source: file, path: pmo/documents/2026-03 - Defect and gap report.md}
---

The March 2026 defect and gap report (`pmo/documents/2026-03 - Defect and gap report.md`) is a draft for "Acme Portal" (as of 2026-03-15) that matches the Acme registers:

- Front matter has `type: defect-gap-report`, `status: draft`, and `period: 2026-03` (quoted or plain).
- The Summary counts are 1 failed test, 3 open issues and 2 requirements without a passing test.
- Defects lists the failed test `TST-002` ("Login with valid credentials"), linked to `REQ-001` and `I-003`; it is never marked passed.
- Open issues lists `I-001`, `I-002` and `I-003`, most severe first, and does not list `I-004` (resolved).
- Gaps lists `REQ-001` ("test failed") and `REQ-002` ("no test"); no entry is invented.
- A missing person or date reads `not set`, `not provided` or `not recorded`; otherwise the person comes from a register or the roster and the date from a register.
