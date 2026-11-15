#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, adds Arabic-Indic digits
# to ar in pmo/config.yaml, updates DEC-2's consequences to "Lower cost by 20 percent" in
# pmo/registers/decisions.yaml, pmo/views/decisions.md and pmo/documents/Decision log.md, and deletes Decision log.ar.md.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
sed -i.bak 's|ar: { label: AR, dir: rtl, glossary: pmo/data/glossary-ar.md }|ar: { label: AR, dir: rtl, glossary: pmo/data/glossary-ar.md, digits: "٠١٢٣٤٥٦٧٨٩" }|' pmo/config.yaml
rm -f pmo/config.yaml.bak
sed -i.bak '/id: DEC-2,/s/consequences: Lower cost,/consequences: Lower cost by 20 percent,/' pmo/registers/decisions.yaml
rm -f pmo/registers/decisions.yaml.bak
sed -i.bak 's/^- \*\*Consequences:\*\* Lower cost$/- **Consequences:** Lower cost by 20 percent/' "pmo/documents/Decision log.md"
rm -f "pmo/documents/Decision log.md.bak"
rm -f "pmo/documents/Decision log.ar.md"
sed -i.bak '/^| DEC-2 |/s/| Lower cost |/| Lower cost by 20 percent |/' pmo/views/decisions.md
rm -f pmo/views/decisions.md.bak
