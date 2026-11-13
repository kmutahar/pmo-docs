#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and inserts a stale recorded hash into the status report draft.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
f="pmo/documents/2026-03 - Status report.md"
awk '{print} /^status: draft$/ {print "source_hashes: {tasks: \"00000000\"}"}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
