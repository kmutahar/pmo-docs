#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, minus its status report draft,
# so any file under pmo/documents/ after the run was written by the agent.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
rm -f "pmo/documents/2026-03 - Status report.md"
