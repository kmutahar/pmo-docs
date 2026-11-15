#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, sets T-1's due date
# to 2026-03-30 and clears its note in pmo/registers/tasks.yaml and pmo/views/tasks.md so T-2
# (due 2026-03-25) is due before T-1 despite dependency D-1.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
sed -i.bak '/id: T-1,/s/due: 2026-03-10, period: 2026-03, notes: Overdue on purpose/due: 2026-03-30, period: 2026-03, notes: ""/' pmo/registers/tasks.yaml
rm -f pmo/registers/tasks.yaml.bak
sed -i.bak '/^| T-1 |/s/| 2026-03-10 |/| 2026-03-30 |/' pmo/views/tasks.md
rm -f pmo/views/tasks.md.bak
