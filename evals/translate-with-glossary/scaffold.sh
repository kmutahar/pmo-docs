#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, turns on French in its config and adds
# an approved French glossary with two terms: "Decision log" and "Open questions". The decision log is set back to
# a draft with no translation (a translation of a draft can be drafted, not finished).
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
# Acme's decision log is finished and translated; this case needs it as a draft without a translation.
sed -i 's/^status: finished$/status: draft/' "pmo/documents/Decision log.md"
sed -i '/^source_hashes:/,/^  decisions:/d' "pmo/documents/Decision log.md"
rm -f "pmo/documents/Decision log.ar.md"
sed -i '/^languages:/,$d' pmo/config.yaml
cat >> pmo/config.yaml <<'EOT'

languages:
  draft: en
  translations: [fr]
  en: { label: EN, dir: ltr }
  fr: { label: FR, dir: ltr, glossary: pmo/data/glossary-fr.md }
EOT
mkdir -p pmo/data
cat > pmo/data/glossary-fr.md <<'EOT'
## Approved

| ID | Term | Translation | Note |
|---|---|---|---|
| G-001 | Decision log | Registre des décisions | document title |
| G-002 | Open questions | Points en suspens | section heading |

## Proposed

| ID | Term | Translation | Seen in | Date |
|---|---|---|---|---|
EOT
