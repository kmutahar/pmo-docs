---
type: llm
weight: 2
focus: {source: file, path: pmo/documents/2026-03 - Client summary.md}
---

The March 2026 client summary (`pmo/documents/2026-03 - Client summary.md`) is a draft for "Acme Portal" (as of 2026-03-15) that matches the Acme registers (plain client wording is fine):

- Front matter has `type: client-summary`, `status: draft`, and `period: 2026-03` (quoted or plain). Draft front matter (`editor: sam`, `template_version`) and template HTML comments (`<!-- ... -->`) are expected in a draft.
- Every section of the client-summary template is present: Where we are, Delivered, Coming next, What we need from you, Changes agreed, Open questions.
- Coming next includes both milestones: Staging ready (due 2026-03-20) and Beta launch (due 2026-04-30).
- What we need from you or Open questions includes the proposed decision to host on the shared cloud, the open vendor delay risk (payment vendor may reply late), and the proposed dark-mode / dark-theme change (not described as agreed or applied).
- Other Acme register items, details and dates (2026-02-10, 2026-02-12, 2026-02-22, 2026-03-01, 2026-03-05, 2026-03-06, 2026-03-08, 2026-03-09, 2026-03-10, 2026-03-25, 2026-04-01) may also appear and are valid (tasks, exit criteria, change impacts, decision reasons, open issues (such as login fails on staging), budget requests, the done API outline, accepted user guide, resolved staging crash, and `None` under Changes agreed), and none is required.
- The prose has no internal ids (`T-001`, `M-001`, `DEC-002` and the like) and no internal team names (`Platform`, `Web`).
- Roster people are Sam Example, Alice Example, and Bob Example.
