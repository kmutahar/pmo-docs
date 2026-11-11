#!/usr/bin/env bash
# Maintainer tool: runs eval cases one at a time through dev/run-evals (Sonnet, one run, no baseline arm) and prints one line per run.
# Full output, results JSON and HTML report stay in ${PMO_LOG_DIR:-$HOME/pmo-logs}/v<version>-evals-<UTC>/<case>-<n>/.
# The version is the one in SKILL.md. Also counts eval-sandbox Bash failures (setgroups) in each run's trace.
# Usage: dev/run-evals-quiet.sh [case ...]   (default: every case in evals/; translation-parity and intake-consent twice)
set -uo pipefail
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then sed -n 2,5p "$0" | sed 's/^# \{0,1\}//'; exit 0; fi
cd "$(dirname "${BASH_SOURCE[0]}")/.."
version="$(sed -n 's/^  version: "\(.*\)"$/\1/p' skills/pmo-docs/SKILL.md | head -1)"
OUT="${PMO_LOG_DIR:-$HOME/pmo-logs}/v$version-evals-$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$OUT"
cases=("$@")
if [ ${#cases[@]} -eq 0 ]; then
  for d in evals/*/case.yaml; do cases+=("$(basename "$(dirname "$d")")"); done
  cases+=(translation-parity intake-consent)  # these two get two runs each
fi
for c in "${cases[@]}"; do
  n=1; while [ -e "$OUT/$c-$n" ]; do n=$((n + 1)); done
  dir="$OUT/$c-$n"; mkdir -p "$dir"
  dev/run-evals --case "$c" --keep-temp --max-cost-usd 0.75 --output-dir "$dir" --report "$dir/report.html" > "$dir/run.log" 2>&1
  python3 - "$dir" "$c-$n" <<'EOF' | tee -a "$OUT/summary.txt"
import json, sys, pathlib
d, name = pathlib.Path(sys.argv[1]), sys.argv[2]
f = d / "aggregate-result.json"
if not f.exists():
    print(f"{name}: NO RESULT (see {d}/run.log)"); sys.exit()
r = json.loads(f.read_text())
for case in r["cases"]:
    for run in case["arms"]["with"]:
        failed = [g["name"] for g in run["graders"] if g.get("scored", True) and not g["passed"]]
        t = pathlib.Path(run.get("tracePath") or "/nonexistent")
        try:
            bash = t.read_text(errors="replace").count("setgroups")
        except OSError:
            bash = "trace not kept"
        print(f"{name}: {'PASS' if run['passed'] else 'FAIL'} score {run['score']:.2f} turns {run['turns']} "
              f"${run['costUsd'] + (run.get('judgeCostUsd') or 0):.2f}"
              + (f" failed: {', '.join(failed)}" if failed else "")
              + (f" error: {str(run['error'])[:80]}" if run.get("error") else "")
              + f" | setgroups in trace: {bash}")
EOF
done
echo "summary: $OUT/summary.txt"
