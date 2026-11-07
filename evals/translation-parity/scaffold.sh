#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, finishes its decision log, enables
# the invented language xx and adds an xx translation with two deliberate faults: the Summary table has one
# row fewer and the date of DEC-1 differs by one digit. The source_hash is the body hash of the original
# (tests/test_eval_translation_parity.py fails when an Acme change moves it). No Python, no network.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
sed -i 's/^status: draft$/status: finished/' "pmo/documents/Decision log.md"
cat >> pmo/config.yaml <<'EOT'

languages:
  draft: en
  translations: [xx]
  en: { label: EN, dir: ltr }
  xx: { label: XX, dir: rtl }
EOT
cat > "pmo/documents/Decision log.xx.md" <<'EOT'
---
title: Decision log - Acme Portal
type: decision-log
project: Acme Portal
manager: Sam Example
template_version: 1
status: draft
last_updated: '2026-03-15'
lang: xx
dir: rtl
translation_of: Decision log.md
source_hash: "f1bea050"
---

# Decisioba log - Acme Portal

## Sumariox
| ID | Decisioba | Statux | Datox | Decidat per |
|---|---|---|---|---|
| DEC-1 | Livrar omni die jovis | acceptato | 2026-02-12 | sam |

## Decisiobaes
### DEC-2 - Hostar sur nubia
- **Statux:** proposito - **Datox:** 2026-03-09 - **Decidat per:** sam
- **Contexto:** Besoing hospitatione barata
- **Decisioba:** Usar computum nubis
- **Optiones consideratas:** partito, proprio
- **Consequentias:** Costo minor
- **Supersedex et relato:** DEC-1

### DEC-1 - Usar livrationes hebdomadales
- **Statux:** acceptato - **Datox:** 2026-02-13 - **Decidat per:** sam
- **Contexto:** Equipa vol livraison constante
- **Decisioba:** Livrar omni die jovis
- **Optiones consideratas:** hebdomadal, mensual
- **Consequentias:** Mutationes minores
- **Supersedex et relato:** nulla

## Questiones apertas
- Nulla ancora.
EOT
