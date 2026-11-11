#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, unchanged. Acme has two meetings,
# MTG-1 (2026-03-09, Weekly sync) and MTG-2 (2026-02-10, Kickoff), and no minutes document.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
