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
from docs_audit import drift_state, register_hash  # noqa: E402


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
    ap.add_argument("--title", help="override the doc type's title in the file name")
    ap.add_argument("--lang", metavar="CODE", help="language code for a translation")
    args = ap.parse_args(argv)

    if args.title is not None and "/" in args.title:
        ap.error("title cannot contain '/'")

    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(args.project)
    doc_types = cfg.get("doc_types", {})
    if args.type not in doc_types:
        ap.error(f"unknown doc type {args.type!r}; known types: {', '.join(sorted(doc_types))}")

    type_trans = pc.type_translations(cfg, args.type)
    tr_flag = pc.translate_flag(cfg, args.type)
    trans_str = ", ".join(type_trans) if type_trans else "none"

    if args.lang:
        if args.lang not in type_trans:
            if type_trans:
                ap.error(f"doc type {args.type!r} does not translate into {args.lang!r}; allowed codes: {', '.join(type_trans)}")
            else:
                ap.error(f"doc type {args.type!r} has no translations configured")

    info = doc_types[args.type]
    title = args.title if args.title is not None else info.get("title", "")
    pattern = info.get("name", "{title}.md")

    try:
        w_start = pc.week_start(cfg)
    except ValueError:
        print("ERROR config: project.week_start must be one of monday..sunday", file=sys.stderr)
        return 2

    try:
        period = pc.resolve_period(args.period, args.week, args.as_of, w_start)
    except ValueError as e:
        ap.error(str(e))

    doc_rel = pc.doc_rel_path(cfg, args.type, period, args.as_of, title=args.title)
    if args.lang:
        trans_doc_rel = pc.translation_rel(doc_rel, args.lang)
        doc_rel_print = trans_doc_rel
        doc_exists = "yes" if (Path(args.project) / trans_doc_rel).exists() else "no"
        orig_exists = "yes" if (Path(args.project) / doc_rel).exists() else "no"
        lang_info = pc.languages(cfg)["info"].get(args.lang, {})
        lang_dir = lang_info.get("dir", "ltr")
        g_app, g_prop = pc.glossary_paths(cfg, args.lang)
    else:
        doc_rel_print = doc_rel
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
    drift = drift_state(args.project, cfg, tpl_path, tpl_source)
    generated_from = ", ".join(info.get("generated_from") or [])
    stale_days = str(info["stale_days"]) if info.get("stale_days") is not None else "none"
    if "{period}" in pattern:
        try:
            first, last = pc.period_range(period, w_start)
            window = f"{first}..{last}"
        except ValueError as e:
            ap.error(str(e))
    else:
        window = "none"

    fields = [
        ("type", args.type),
        ("title", title),
        ("document", doc_rel_print),
        ("document_exists", doc_exists),
    ]
    if args.lang:
        fields.extend([
            ("original", doc_rel),
            ("original_exists", orig_exists),
            ("translation_of", f'"{doc_rel[len(cfg["paths"]["documents"]) + 1:]}"'),  # relative to paths.documents (doc_rel_path joins them with "/")
            ("lang", args.lang),
            ("dir", lang_dir),
            ("glossary", g_app if g_app else "none"),
            ("glossary_proposed", g_prop if g_prop else "none"),
        ])
    fields.extend([
        ("template", template_str),
        ("template_source", tpl_source),
        ("template_exists", tpl_exists),
        ("template_version", tpl_version),
        ("based_on", based_on),
        ("drift", drift),
        ("generated_from", generated_from),
        ("stale_days", stale_days),
        ("window", window),
        ("translations", trans_str),
        ("translate", tr_flag),
    ])
    if args.hashes:
        if args.lang:
            orig_path = Path(args.project) / doc_rel
            if orig_path.is_file():
                h = pc.body_hash(pc.read(orig_path))
                fields.append(("source_hash", f'"{h}"'))
            else:
                fields.append(("source_hash", "none"))
        elif info.get("generated_from"):
            pairs = ", ".join(f'{r}: "{register_hash(args.project, cfg, r)}"' for r in info["generated_from"])
            fields.append(("source_hashes", "{" + pairs + "}"))
    for k, v in fields:
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
