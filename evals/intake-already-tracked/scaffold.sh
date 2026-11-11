#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and adds a short fake chat export,
# inbox/chat-export.txt, with Acme people only: a request that matches task T-2 (already tracked), a message
# that the vendor of T-4 is picked (a status change, only a proposal) and one new task for Alice.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
mkdir -p inbox
cat > inbox/chat-export.txt <<'EOT'
[2026-03-13 09:02] Sam Example: Bob, please design the login page, due 2026-03-25
[2026-03-13 09:10] Bob Example: will do
[2026-03-14 16:20] Bob Example: the budget came through, so the payment vendor is picked
[2026-03-15 10:05] Sam Example: Alice, please write the rollback notes for the beta, due 2026-04-03
[2026-03-15 10:06] Alice Example: ok
EOT
