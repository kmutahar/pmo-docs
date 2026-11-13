#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, configures publishing,
# finishes the March status report, and installs the pmo/bin/pmo launcher for a skill-only install.
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
# In a clone the skill is at skills/pmo-docs; under dev/run-evals it is the plugin root.
skill="$here/../../skills/pmo-docs"; [ -d "$skill" ] || skill="$here/../.."
doc="pmo/documents/2026-03 - Status report.md"
hashes="$(python3 "$skill/scripts/where.py" status-report 2026-03 --hashes | sed -n 's/^source_hashes: //p')"
sed -i.bak -e 's/^status: draft/status: finished/' -e "s/^last_updated: .*/&\nsource_hashes: $hashes/" "$doc"
rm -f "$doc.bak"
mkdir -p pmo/bin
cp "$skill/assets/starter/bin/pmo" pmo/bin/pmo
chmod +x pmo/bin/pmo
