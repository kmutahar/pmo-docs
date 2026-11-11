#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, minus its March status report, so
# there is no previous report and the weekly report for 2026-W10 is the first one.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
rm -f "pmo/documents/2026-03 - Status report.md"
