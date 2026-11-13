#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, adds the fake Express app under src/, removes any API reference draft, and clears technical.stacks.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
mkdir -p src
cp -R "$here/../technical-draft-reads-code/app/." src/
printf '%s\n' 'API_KEY=Example-Key-zz-1234' > src/.env
printf '%s\n' 'API_KEY=' > src/.env.example
rm -f "pmo/documents/API reference.md"
sed -i.bak 's/^  stacks: \[express\]/  stacks: []/' pmo/config.yaml && rm -f pmo/config.yaml.bak
