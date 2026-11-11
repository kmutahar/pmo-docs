#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, turns on French in its config and adds
# an approved French glossary with two terms: "Decision log" and "Open questions". The decision log stays a
# draft (a translation of a draft can be drafted, not finished). No translation exists yet.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
cat >> pmo/config.yaml <<'EOT'

languages:
  draft: en
  translations: [fr]
  en: { label: EN, dir: ltr }
  fr: { label: FR, dir: ltr, glossary: pmo/data/glossary-fr.md }
EOT
mkdir -p pmo/data
cat > pmo/data/glossary-fr.md <<'EOT'
| Term | Translation | Note |
|---|---|---|
| Decision log | Registre des décisions | document title |
| Open questions | Points en suspens | section heading |
EOT
