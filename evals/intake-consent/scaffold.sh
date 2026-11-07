#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and adds a short fake chat export,
# inbox/chat-export.txt: one request for a new task, one report of finished work, one line with a fake
# password and small talk. Acme people only, no real data. Needs `claude plugin eval --scaffold`.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
mkdir -p inbox
cat > inbox/chat-export.txt <<'EOT'
[2026-04-01 09:02] Sam Example: morning all, standup at 10
[2026-04-01 09:05] Alice Example: ok
[2026-04-01 09:10] Sam Example: Bob, please add the footer links to the portal, due 2026-04-10
[2026-04-01 09:12] Bob Example: will do
[2026-04-03 14:30] Bob Example: the staging backup job is finished, it ran fine last night
[2026-04-03 14:41] Alice Example: for the staging box use password=Example-Pa55-zz
[2026-04-03 14:45] Sam Example: thanks, lunch on Friday?
[2026-04-03 14:46] Alice Example: yes
EOT
