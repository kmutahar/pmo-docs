#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and removes the due date of task T-2
# in the copy (never in examples/acme) and updates pmo/views/tasks.md so it matches. Expected as of 2026-03-26:
# one overdue task (T-1, 16 days late), one action past due (ACT-1), one milestone (M-1), three open issues,
# one open risk and one open task without a due date (T-2). No Python, no network.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
sed -i.bak '/id: T-2,/s/ due: 2026-03-25,//' pmo/registers/tasks.yaml
rm -f pmo/registers/tasks.yaml.bak
sed -i.bak '/^| T-2 |/s/| 2026-03-25 |$/|  |/' pmo/views/tasks.md
rm -f pmo/views/tasks.md.bak
