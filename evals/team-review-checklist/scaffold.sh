#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder and adds one Proposed glossary row.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
printf '| G-019 | Staging | بيئة الاختبار | T-001 | 2026-03-01 |\n' >> pmo/data/glossary-ar.md
