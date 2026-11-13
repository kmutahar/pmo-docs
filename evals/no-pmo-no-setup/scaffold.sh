#!/usr/bin/env bash
# Builds a code-only folder with no pmo/ folder. Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p src
printf 'def main():\n    return 1\n' > src/app.py
