#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, changes task T-001's owner
# to bob in the copy so bob owns all open tasks, and updates pmo/views/tasks.md to match.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
sed -i.bak '/id: T-001,/s/owner: alice/owner: bob/' pmo/registers/tasks.yaml
rm -f pmo/registers/tasks.yaml.bak
sed -i.bak '/^| T-001 |/s/| alice |/| bob |/' pmo/views/tasks.md
rm -f pmo/views/tasks.md.bak
