#!/usr/bin/env bash
# Copies Acme and adds a two-sided merge conflict on T-2 in pmo/registers/tasks.yaml. Needs `claude plugin eval --scaffold`. Uses only the repo's fixture, no real data.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../examples/acme/." .
python3 - <<'PY'
import re
from pathlib import Path
p = Path("pmo/registers/tasks.yaml")
lines = p.read_text(encoding="utf-8").split("\n")
i = next(n for n, line in enumerate(lines) if re.search(r"id: T-2[,}]", line))
ours = lines[i].replace("status: not-started", "status: in-progress")
theirs = lines[i].replace("due: 2026-03-25", "due: 2026-04-02")
assert ours != lines[i] and theirs != lines[i]
lines[i:i + 1] = ["<<<<<<< HEAD", ours, "=======", theirs, ">>>>>>> feature/login-dates"]
p.write_text("\n".join(lines), encoding="utf-8")
PY
