#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, configures publishing,
# and finishes the March status report: status finished plus the source_hashes the Finish playbook records,
# so the document is new for publish.py, not stale. No Python, no network.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
cat <<'EOF' >> pmo/config.yaml

publish:
  mode: folder
  path: published
  url: null
EOF
doc="pmo/documents/2026-03 - Status report.md"
hashes=""
for reg in tasks milestones risks issues changes actions decisions teams; do
  h="$( { sha256sum "pmo/registers/$reg.yaml" 2>/dev/null || shasum -a 256 "pmo/registers/$reg.yaml"; } | cut -c1-8)"
  hashes="$hashes$reg: \"$h\", "
done
sed -i.bak -e 's/^status: draft/status: finished/' -e "s/^last_updated: .*/&\nsource_hashes: {${hashes%, }}/" "$doc"
rm -f "$doc.bak"
