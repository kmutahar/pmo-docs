#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and finishes its March status report
# with the source_hashes of the registers as they are now, so the only audit finding is its age: last_updated
# 2026-03-15 and a limit of 30 days (stale_days of status-report). The hash is the first 8 hex characters of
# the SHA-256 of the register file, as the Finish playbook records it. No Python, no network.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
doc="pmo/documents/2026-03 - Status report.md"
hashes=""
for reg in tasks milestones risks issues changes actions decisions teams; do
  hashes="$hashes$reg: \"$(sha256sum "pmo/registers/$reg.yaml" | cut -c1-8)\", "
done
sed -i.bak -e 's/^status: draft/status: finished/' -e "s/^last_updated: .*/&\nsource_hashes: {${hashes%, }}/" "$doc"
rm -f "$doc.bak"
