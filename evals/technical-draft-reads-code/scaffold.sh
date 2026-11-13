#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, adds a tiny fake Express app under src/, and removes any API reference draft.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
mkdir -p src
cp -R "$here/app/." src/
printf '%s\n' 'API_KEY=Example-Key-zz-1234' > src/.env
printf '%s\n' 'API_KEY=' > src/.env.example
rm -f "pmo/documents/API reference.md"
