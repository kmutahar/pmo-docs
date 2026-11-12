#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .

echo "alice" > pmo/.me
sed -i 's/^type: status-report/type: status-report\neditor: bob/' "pmo/documents/2026-03 - Status report.md"
