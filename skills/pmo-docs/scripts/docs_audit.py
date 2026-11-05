#!/usr/bin/env python3
"""Mechanical documentation audit. Prints a Markdown report, exits 1 when there are findings
(2 for a usage error, including a project folder that does not exist).

Usage:
    python3 docs_audit.py [--project ROOT] [--as-of YYYY-MM-DD]

Walks the documents folder (paths.documents). A document's type is its front-matter `type` and must
be a doc type in the config. Checks:
  front matter  `type` is present and is a known doc type
  stale         a document with `status: finished` is stale when the hash recorded in its front matter for any
                register in the type's `generated_from` differs from the register's current hash
  old           a finished document is older than its type's `stale_days` (front-matter
                `last_updated`; a finished document without it is a front-matter finding)
  broken links  relative Markdown links that point at a missing file

Recorded hashes (written by the Finish step) live in front matter as
    source_hashes: {tasks: "ab12cd34", risks: "0f9e8d7c"}
Each value is the first 8 hex characters of the SHA-256 of the register file's bytes
(see register_hash); a register file that does not exist hashes to "none". Quote the values: an
all-digit hash such as 12345678 would be read as a number and is reported as "quote the hash".
Docs-vs-code drift is not mechanical: the docs-audit playbook covers it.
"""
import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pmo_common as pc  # noqa: E402


def _unquote(s):
    """Decode %XX escapes in a link target (UTF-8)."""
    return re.sub(r"(?:%[0-9A-Fa-f]{2})+", lambda m: bytes.fromhex(m[0].replace("%", "")).decode("utf-8", "replace"), s)


CHECKS = ("front matter", "stale", "old", "broken links")


def register_hash(root, cfg, name):
    """8 hex characters of the SHA-256 of a register's file, or "none" when the file is missing."""
    f = Path(root) / cfg["paths"]["registers"] / cfg["registers"][name]["file"]
    return hashlib.sha256(f.read_bytes()).hexdigest()[:8] if f.exists() else "none"


def audit_file(root, cfg, path, base, today):
    """[(check, message)] for one document."""
    rel = path.relative_to(base)
    out = []
    text = pc.read(path)
    fm, _ = pc.split_front_matter(text)
    if fm is None:
        return [("front matter", f"`{rel}` - no front matter")]
    ty = fm.get("type")
    if not ty:
        out.append(("front matter", f"`{rel}` - front matter has no `type`"))
    t = cfg["doc_types"].get(ty) if isinstance(ty, str) else None
    if ty and not t:
        out.append(("front matter", f"`{rel}` - type `{fm['type']}` is not a doc type in the config"))
    if t and fm.get("status") == "finished":
        recorded = fm.get("source_hashes") or {}
        if not isinstance(recorded, dict):
            out.append(("front matter", f"`{rel}` - source_hashes must be a map of register to hash"))
            recorded = {}
        for reg in t.get("generated_from") or []:
            if reg not in cfg["registers"]:
                continue
            if reg not in recorded:
                out.append(("stale", f"`{rel}` - no recorded hash for register `{reg}`"))
            elif not isinstance(recorded[reg], str):
                out.append(("front matter", f"`{rel}` - recorded hash for register `{reg}` is not text: quote the hash"))
            elif recorded[reg] != register_hash(root, cfg, reg):
                out.append(("stale", f"`{rel}` - register `{reg}` changed since the document was finished"))
        try:
            stamp = pc.to_date(fm.get("last_updated"))
        except ValueError:
            stamp = None
            out.append(("front matter", f"`{rel}` - last_updated is not a YYYY-MM-DD date"))
        else:
            if stamp is None:
                out.append(("front matter", f"`{rel}` - finished but has no `last_updated`"))
        if stamp and t.get("stale_days") and (today - stamp).days > t["stale_days"]:
            out.append(("old", f"`{rel}` - {(today - stamp).days} days old (limit {t['stale_days']})"))
    for target in re.findall(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)", text):
        if not (path.parent / _unquote(target.split("#")[0])).exists():
            out.append(("broken links", f"`{rel}` -> `{target}`"))
    return out


def audit(root, cfg, today):
    """(files scanned, {check: [message]})."""
    base = Path(root) / cfg["paths"]["documents"]
    files = sorted(base.rglob("*.md")) if base.exists() else []
    found = {c: [] for c in CHECKS}
    for p in files:
        for check, msg in audit_file(root, cfg, p, base, today):
            found[check].append(msg)
    return len(files), found


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mechanical documentation audit; exits 1 on findings.")
    pc.add_project_arg(ap)
    ap.add_argument("--as-of", type=datetime.date.fromisoformat, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date used for age checks (default: today)")
    args = ap.parse_args(argv)
    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")
    cfg = pc.load_config(args.project)
    count, found = audit(args.project, cfg, args.as_of)
    print(f"# Docs audit - {args.as_of}\n\nScanned {count} Markdown files.\n")
    total = 0
    for check, items in found.items():
        total += len(items)
        print(f"## {check.capitalize()} ({len(items)})\n")
        print("\n".join(f"- {x}" for x in items) if items else "None")
        print()
    print(f"**Total findings: {total}**")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
