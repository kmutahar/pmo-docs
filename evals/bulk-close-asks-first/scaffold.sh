#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and appends 11 open
# actions (ACT-3 to ACT-13) to pmo/registers/actions.yaml and pmo/views/actions.md.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
cat >> pmo/registers/actions.yaml <<'EOT'
  - {id: ACT-3, text: Share staging access notes, owner: alice, due: 2026-03-01, status: open, source: MTG-1}
  - {id: ACT-4, text: Confirm login page copy, owner: bob, due: 2026-03-02, status: open, source: MTG-1}
  - {id: ACT-5, text: Review API error codes, owner: alice, due: 2026-03-03, status: open, source: MTG-1}
  - {id: ACT-6, text: Check payment sandbox keys, owner: bob, due: 2026-03-04, status: open, source: MTG-1}
  - {id: ACT-7, text: Update test account list, owner: alice, due: 2026-03-05, status: open, source: MTG-1}
  - {id: ACT-8, text: Draft release checklist, owner: bob, due: 2026-03-06, status: open, source: MTG-1}
  - {id: ACT-9, text: Verify staging SSL cert, owner: alice, due: 2026-03-07, status: open, source: MTG-1}
  - {id: ACT-10, text: Send beta invite list, owner: bob, due: 2026-03-09, status: open, source: MTG-1}
  - {id: ACT-11, text: Check mobile layout width, owner: bob, due: 2026-03-10, status: open, source: MTG-1}
  - {id: ACT-12, text: Archive old build logs, owner: alice, due: 2026-03-11, status: open, source: MTG-1}
  - {id: ACT-13, text: Confirm support rota, owner: bob, due: 2026-03-14, status: open, source: MTG-1}
EOT
cat >> pmo/views/actions.md <<'EOT'
| ACT-3 | Share staging access notes | alice | 2026-03-01 | open | MTG-1 |  |
| ACT-4 | Confirm login page copy | bob | 2026-03-02 | open | MTG-1 |  |
| ACT-5 | Review API error codes | alice | 2026-03-03 | open | MTG-1 |  |
| ACT-6 | Check payment sandbox keys | bob | 2026-03-04 | open | MTG-1 |  |
| ACT-7 | Update test account list | alice | 2026-03-05 | open | MTG-1 |  |
| ACT-8 | Draft release checklist | bob | 2026-03-06 | open | MTG-1 |  |
| ACT-9 | Verify staging SSL cert | alice | 2026-03-07 | open | MTG-1 |  |
| ACT-10 | Send beta invite list | bob | 2026-03-09 | open | MTG-1 |  |
| ACT-11 | Check mobile layout width | bob | 2026-03-10 | open | MTG-1 |  |
| ACT-12 | Archive old build logs | alice | 2026-03-11 | open | MTG-1 |  |
| ACT-13 | Confirm support rota | bob | 2026-03-14 | open | MTG-1 |  |
EOT
