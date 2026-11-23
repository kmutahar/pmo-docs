#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, unchanged. Acme has changes CR-001 and CR-002,
# so the next id is CR-003, and task T-002 is due 2026-03-25.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
