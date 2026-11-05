#!/usr/bin/env python3
"""Print where a document, its template and its inputs live.

Usage:
    python3 where.py <type> [period] [--week] [--as-of YYYY-MM-DD] [--hashes] [--project ROOT]
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
from docs_audit import register_hash  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find where a document, its template and its inputs live.")
    pc.add_project_arg(ap)
    ap.add_argument("type", help="document type (e.g. status-report)")
    ap.add_argument("period", nargs="?", default=None, help="period string (e.g. 2026-03)")
    ap.add_argument("--week", action="store_true", help="use ISO week as period (YYYY-Www)")
    ap.add_argument("--as-of", type=datetime.date.fromisoformat, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date to evaluate period against (default: today)")
    ap.add_argument("--hashes", action="store_true",
                    help="also print source_hashes: the Finish value for the type's generated_from registers")
    args = ap.parse_args(argv)

    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(args.project)
    doc_types = cfg.get("doc_types", {})
    if args.type not in doc_types:
        ap.error(f"unknown doc type {args.type!r}; known types: {', '.join(sorted(doc_types))}")

    info = doc_types[args.type]
    title = info.get("title", "")
    pattern = info.get("name", "{title}.md")

    if args.period:
        if not re.fullmatch(r"[0-9]{4}-([0-9]{2}|W[0-9]{2})", args.period):
            ap.error(f"invalid period {args.period!r}; use YYYY-MM or YYYY-Www")
        period = args.period
    elif args.week:
        # shortcut: ISO weeks start on Monday, no per-project week start; add one when a project needs Sunday weeks
        iso = args.as_of.isocalendar()
        period = f"{iso.year}-W{iso.week:02d}"
    else:
        period = args.as_of.strftime("%Y-%m")

    doc_file = pattern.replace("{title}", title).replace("{period}", period).replace("{date}", str(args.as_of))
    doc_rel = f"{cfg['paths']['documents']}/{doc_file}"
    doc_exists = "yes" if (Path(args.project) / doc_rel).exists() else "no"

    tpl_name = info.get("template", f"{args.type}.md")
    tpl_path, tpl_source = pc.find_asset(args.project, cfg, "templates", tpl_name)
    if tpl_source == "project":
        template_str = tpl_path.relative_to(Path(args.project)).as_posix()
    else:
        template_str = str(tpl_path.resolve())

    tpl_exists = "yes" if tpl_path.exists() else "no"
    fm = {}
    if tpl_path.exists():
        try:
            fm = pc.split_front_matter(pc.read(tpl_path))[0] or {}
        except Exception:
            fm = {}

    tpl_version = str(fm.get("template_version")) if fm.get("template_version") is not None else "none"
    based_on = str(fm.get("based_on")) if fm.get("based_on") is not None else "none"
    generated_from = ", ".join(info.get("generated_from") or [])
    stale_days = str(info["stale_days"]) if info.get("stale_days") is not None else "none"

    fields = [
        ("type", args.type),
        ("title", title),
        ("document", doc_rel),
        ("document_exists", doc_exists),
        ("template", template_str),
        ("template_source", tpl_source),
        ("template_exists", tpl_exists),
        ("template_version", tpl_version),
        ("based_on", based_on),
        ("generated_from", generated_from),
        ("stale_days", stale_days),
    ]
    if args.hashes and info.get("generated_from"):
        pairs = ", ".join(f'{r}: "{register_hash(args.project, cfg, r)}"' for r in info["generated_from"])
        fields.append(("source_hashes", "{" + pairs + "}"))
    for k, v in fields:
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
