#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, removes the due date of task T-2
# in the copy (never in examples/acme) and re-renders the views so they match.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
sed -i.bak '/id: T-2,/s/ due: 2026-03-25,//' pmo/registers/tasks.yaml
rm -f pmo/registers/tasks.yaml.bak
python3 "$here/../../skills/pmo-docs/scripts/render_views.py" > /dev/null
