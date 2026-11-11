#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and makes the March status report ready
# to finish in the copy: its open question becomes "None" and a template comment (which Finish removes) sits
# above the title. Finishing needs where.py --hashes and structure_check.py, which cannot run in the eval sandbox.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
doc="pmo/documents/2026-03 - Status report.md"
sed -i.bak -e 's/^- Who approves the budget for the vendor?$/- None/' \
  -e 's/^# Status report - Acme Portal$/<!-- Reads: tasks, milestones, risks, issues, changes -->\n\n&/' "$doc"
rm -f "$doc.bak"
