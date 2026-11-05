#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, keeps its March status report
# and appends one line a person added by hand that no register holds.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
printf '\n- Note added by hand: the vendor demo moved to Friday.\n' >> "pmo/documents/2026-03 - Status report.md"
