#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, makes it a git repo with one
# commit, then changes task T-2's status to in-progress in pmo/registers/tasks.yaml and pmo/views/tasks.md.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
git init -q -b main
git add -A
git -c user.name=Eval -c user.email=noreply -c commit.gpgsign=false commit -q -m "fixture"
sed -i.bak '/id: T-2,/s/status: not-started/status: in-progress/' pmo/registers/tasks.yaml
rm -f pmo/registers/tasks.yaml.bak
sed -i.bak \
  -e 's/not-started 1, in-progress 1,/not-started 0, in-progress 2,/' \
  -e '/^| medium |/s/| 2 | 1 | 0 |/| 2 | 0 | 1 |/' \
  -e '/^| T-2 |/s/| not-started |/| in-progress |/' \
  pmo/views/tasks.md
rm -f pmo/views/tasks.md.bak
