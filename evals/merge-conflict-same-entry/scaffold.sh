#!/usr/bin/env bash
# Copies Acme and adds a two-sided merge conflict on T-002 in pmo/registers/tasks.yaml. No Python, no network. Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
awk '
/id: T-002[,}]/ {
  ours = $0; sub(/status: not-started/, "status: in-progress", ours)
  theirs = $0; sub(/due: 2026-03-25/, "due: 2026-04-02", theirs)
  if (ours == $0 || theirs == $0) exit 1
  print "<<<<<<< HEAD"
  print ours
  print "======="
  print theirs
  print ">>>>>>> feature/login-dates"
  found = 1
  next
}
{ print }
END { if (!found) exit 1 }
' pmo/registers/tasks.yaml > pmo/registers/tasks.yaml.tmp && mv pmo/registers/tasks.yaml.tmp pmo/registers/tasks.yaml
