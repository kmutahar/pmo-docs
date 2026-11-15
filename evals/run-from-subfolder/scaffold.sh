#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and creates docs/notes.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
mkdir -p docs/notes
