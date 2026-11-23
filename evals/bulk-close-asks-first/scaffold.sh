#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and appends 11 open
# actions (ACT-003 to ACT-013) to pmo/registers/actions.yaml and pmo/views/actions.md.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
cat >> pmo/registers/actions.yaml <<'EOT'
  - {id: ACT-003, text: Share staging access notes, owner: alice, due: 2026-03-01, status: open, source: MTG-001}
  - {id: ACT-004, text: Confirm login page copy, owner: bob, due: 2026-03-02, status: open, source: MTG-001}
  - {id: ACT-005, text: Review API error codes, owner: alice, due: 2026-03-03, status: open, source: MTG-001}
  - {id: ACT-006, text: Check payment sandbox keys, owner: bob, due: 2026-03-04, status: open, source: MTG-001}
  - {id: ACT-007, text: Update test account list, owner: alice, due: 2026-03-05, status: open, source: MTG-001}
  - {id: ACT-008, text: Draft release checklist, owner: bob, due: 2026-03-06, status: open, source: MTG-001}
  - {id: ACT-009, text: Verify staging SSL cert, owner: alice, due: 2026-03-07, status: open, source: MTG-001}
  - {id: ACT-010, text: Send beta invite list, owner: bob, due: 2026-03-09, status: open, source: MTG-001}
  - {id: ACT-011, text: Check mobile layout width, owner: bob, due: 2026-03-10, status: open, source: MTG-001}
  - {id: ACT-012, text: Archive old build logs, owner: alice, due: 2026-03-11, status: open, source: MTG-001}
  - {id: ACT-013, text: Confirm support rota, owner: bob, due: 2026-03-14, status: open, source: MTG-001}
EOT
cat >> pmo/views/actions.md <<'EOT'
| ACT-003 | Share staging access notes | alice | 2026-03-01 | open | MTG-001 |  |
| ACT-004 | Confirm login page copy | bob | 2026-03-02 | open | MTG-001 |  |
| ACT-005 | Review API error codes | alice | 2026-03-03 | open | MTG-001 |  |
| ACT-006 | Check payment sandbox keys | bob | 2026-03-04 | open | MTG-001 |  |
| ACT-007 | Update test account list | alice | 2026-03-05 | open | MTG-001 |  |
| ACT-008 | Draft release checklist | bob | 2026-03-06 | open | MTG-001 |  |
| ACT-009 | Verify staging SSL cert | alice | 2026-03-07 | open | MTG-001 |  |
| ACT-010 | Send beta invite list | bob | 2026-03-09 | open | MTG-001 |  |
| ACT-011 | Check mobile layout width | bob | 2026-03-10 | open | MTG-001 |  |
| ACT-012 | Archive old build logs | alice | 2026-03-11 | open | MTG-001 |  |
| ACT-013 | Confirm support rota | bob | 2026-03-14 | open | MTG-001 |  |
EOT
