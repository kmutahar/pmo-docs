#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .

cat << 'EOF' >> pmo/registers/tasks.yaml
  - {id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03}
  - {id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03}
EOF

cat << 'EOF' >> pmo/registers/changes.yaml
  - {id: CR-3, title: Fix login timeout on mobile, requested_by: bob, date: 2026-03-08, description: Timeout fix, impact: Fast fix, status: proposed, decided_by: null, decided_on: null, related_tasks: [T-5]}
EOF

cat << 'EOF' >> pmo/registers/dependencies.yaml
  - {id: D-3, type: internal, from: T-5, to: T-3, text: Release notes need API outline, status: open}
EOF
