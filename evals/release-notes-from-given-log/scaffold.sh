#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, unchanged. The commit log the case
# needs is in prompt.md (made-up hashes), because git does not run in the eval sandbox.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
