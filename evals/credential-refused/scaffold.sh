#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, unchanged. Acme has environments
# ENV-001 and ENV-002, so the next id is ENV-003. The fake password is in prompt.md.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
