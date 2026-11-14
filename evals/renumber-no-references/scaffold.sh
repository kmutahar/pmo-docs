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
