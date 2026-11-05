#!/usr/bin/env bash
# Copies the fake Acme project (examples/acme) into the working folder, makes it a git repo with one
# commit, and adds one untracked file. The commit uses a throwaway identity set only for this command.
# Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
git init -q -b main
git add -A
git -c user.name=Eval -c user.email=noreply -c commit.gpgsign=false commit -q -m "fixture"
echo "- ask the vendor about the test account" > scratch-notes.txt
