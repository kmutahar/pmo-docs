#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, removes the March status report (so it can
# be drafted again) and adds pmo/house-rules.md with a RAG rule that replaces the default one. As of 2026-03-15 the
# default rule gives red (task T-1 is overdue); this rule gives amber (a task is overdue, no milestone is: M-1 is due
# 2026-03-20).
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
rm -f "pmo/documents/2026-03 - Status report.md"
cat > pmo/house-rules.md <<'EOT'
# House rules

## RAG for status reports
Replace the default RAG rule with this one:
- Red only when a milestone is overdue.
- Amber when any task is blocked or overdue, and no milestone is overdue.
- Green otherwise.
EOT
