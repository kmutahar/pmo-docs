#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, unchanged. Acme has open tasks T-1 (high),
# T-2 and T-4 (medium), the in-progress milestone M-1 due 2026-03-20, and no delivery report for 2026-03.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
