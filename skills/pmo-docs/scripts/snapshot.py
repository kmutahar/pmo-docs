#!/usr/bin/env python3
"""Write a snapshot of the registers, for `where.py --delta` and the status report.

Usage:
    python3 snapshot.py [--as-of YYYY-MM-DD] [--project ROOT]

Writes <paths.snapshots>/<date>.json (default date: today; a snapshot of the same day is replaced). It holds each register's hash and, for the tasks, risks, issues and actions registers, only each entry's id and status (no titles or other text). Prints the path.

Exit codes: 0 ok, 2 usage, a config the skill refuses, or a register that cannot be read.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
from docs_audit import register_hash  # noqa: E402

TRACKED = ("tasks", "risks", "issues", "actions")


def take(root, cfg, day):
    """The snapshot of the registers as a dict."""
    entries = {}
    for r in TRACKED:
        if r in cfg["registers"]:
            entries[r] = {str(e["id"]): str(e.get("status", "none")) for e in pc.load_register(root, cfg, r) if isinstance(e, dict) and "id" in e}
    return {"date": str(day), "hashes": {r: register_hash(root, cfg, r) for r in sorted(cfg["registers"])}, "entries": entries}


def delta(root, cfg, as_of):
    """Output lines for what changed since the latest snapshot dated before as_of; one line `delta: no snapshot` when there is none."""
    d = Path(root) / cfg["paths"]["snapshots"]
    files = sorted(f for f in d.glob("????-??-??.json") if f.stem < str(as_of)) if d.is_dir() else []
    if not files:
        return ["delta: no snapshot"]
    old = json.loads(pc.read(files[-1]))["entries"]
    new = take(root, cfg, as_of)["entries"]
    lines = [f"delta: since {files[-1].stem}"]
    for r in TRACKED:
        if r not in old or r not in new:
            continue
        o, n = old[r], new[r]
        for kind, items in (("changed", [f"{i} {o[i]}->{n[i]}" for i in n if i in o and o[i] != n[i]]),
                            ("added", [f"{i} {n[i]}" for i in n if i not in o]),
                            ("removed", [f"{i} {o[i]}" for i in o if i not in n])):
            if items:
                lines.append(f"{kind}_{r}: {', '.join(items)}")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("--as-of", type=pc.as_of, default=datetime.date.today(), metavar="YYYY-MM-DD", help="snapshot date (default: today)")
    args = ap.parse_args(argv)
    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")
    cfg = pc.load_config(args.project)
    rel = f"{cfg['paths']['snapshots']}/{args.as_of}.json"
    try:
        snap = take(args.project, cfg, args.as_of)
    except ValueError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    pc.check_inside(args.project, rel)
    (Path(args.project) / rel).parent.mkdir(parents=True, exist_ok=True)
    pc.safe_write(args.project, rel, json.dumps(snap, indent=2, sort_keys=True) + "\n")
    print(rel)
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
