#!/usr/bin/env python3
"""Print where a document, its template and its inputs live.

Usage:
    python3 where.py <type> [period] [--week] [--as-of YYYY-MM-DD] [--hashes] [--title TEXT] [--lang CODE] [--subproject ID] [--project ROOT]
    python3 where.py --delta [--as-of YYYY-MM-DD] [--project ROOT]

--delta needs no type. It prints what changed in the tasks, risks, issues and actions registers since the latest snapshot before the as-of date (snapshot.py writes them): `delta: since DATE`, then `changed_<register>: ID old->new`, `added_<register>: ID status` and `removed_<register>: ID status` lines; or `delta: no snapshot` when there is none.

--subproject is for a doc type with per_subproject: true (required for it): it fills {subproject} in the name and adds an `entries_<register>` line (ids) per generated_from register whose `subproject` field matches.

Prints key: value lines, then one `subproject: <id> kind=.. stack=.. docs_dir=..` line per sub-project in the config (unset parts are left out).

Exit codes: 0 ok, 2 usage, a config the skill refuses, or a template that is not UTF-8 text.
"""
import argparse
import datetime
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
from docs_audit import drift_state, register_hash  # noqa: E402
from snapshot import delta  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("type", nargs="?", help="document type (e.g. status-report)")
    ap.add_argument("period", nargs="?", default=None, help="period string (e.g. 2026-03)")
    ap.add_argument("--week", action="store_true", help="use ISO week as period (YYYY-Www)")
    ap.add_argument("--as-of", type=pc.as_of, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date to evaluate period against (default: today)")
    ap.add_argument("--hashes", action="store_true",
                    help="also print source_hashes: the Finish value for the type's generated_from registers")
    ap.add_argument("--title", help="override the doc type's title in the file name")
    ap.add_argument("--lang", metavar="CODE", help="language code for a translation")
    ap.add_argument("--delta", action="store_true", help="print what changed in the tasks, risks, issues and actions since the latest snapshot (no type needed)")
    ap.add_argument("--subproject", metavar="ID", help="for a per_subproject doc type: the sub-project the document is about")
    args = ap.parse_args(argv)

    if args.delta:
        if not Path(args.project).is_dir():
            ap.error(f"project folder not found: {args.project}")
        try:
            print("\n".join(delta(args.project, pc.load_config(args.project), args.as_of)))
        except ValueError as e:
            print(f"ERROR {e}", file=sys.stderr)
            return 2
        return 0
    if not args.type:
        ap.error("the following arguments are required: type")

    if args.title is not None and not args.title.strip():
        ap.error("title cannot be empty")
    if args.title is not None and "/" in args.title:
        ap.error("title cannot contain '/'")

    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(args.project)
    doc_types = cfg.get("doc_types", {})
    if args.type not in doc_types:
        ap.error(f"unknown doc type {args.type!r}; known types: {', '.join(sorted(doc_types))}")

    if err := pc.subproject_error(cfg, args.type, args.subproject):
        ap.error(err)

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

    doc_rel = pc.doc_rel_path(cfg, args.type, period, args.as_of, title=args.title, subproject=args.subproject)
    if args.lang:
        try:
            trans_doc_rel = pc.translation_rel(doc_rel, args.lang)
        except ValueError as e:
            print(f"ERROR {e}", file=sys.stderr)
            return 2
        doc_rel_print = trans_doc_rel
        doc_exists = "yes" if (Path(args.project) / trans_doc_rel).exists() else "no"
        orig_exists = "yes" if (Path(args.project) / doc_rel).exists() else "no"
        lang_info = pc.languages(cfg)["info"].get(args.lang, {})
        lang_dir = lang_info.get("dir", "ltr")
        g_app = pc.glossary_path(cfg, args.lang)
        n_app = pc.names_path(cfg, args.lang)
    else:
        doc_rel_print = doc_rel
        doc_exists = "yes" if (Path(args.project) / doc_rel).exists() else "no"

    tpl_name = info.get("template", f"{args.type}.md")
    try:
        tpl_path, tpl_source = pc.find_asset(args.project, cfg, "templates", tpl_name)
    except ValueError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
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
    try:
        drift = drift_state(args.project, cfg, tpl_path, tpl_source)
    except UnicodeDecodeError:
        print(f"template {tpl_path.name}: not UTF-8 text", file=sys.stderr)
        return 2
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
            # shortcut: doc_rel is generated by doc_rel_path, so string slice is safe and avoids ValueError on mismatch
            ("translation_of", f'"{doc_rel[len(cfg["paths"]["documents"]) + 1:]}"'),  # relative to paths.documents (doc_rel_path joins them with "/")
            ("lang", args.lang),
            ("dir", lang_dir),
            ("glossary", g_app if g_app else "none"),
            ("names", n_app if n_app else "none"),
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
            pairs = ", ".join(f'{r}: "{register_hash(args.project, cfg, r)}"' for r in info["generated_from"] if r in cfg["registers"])
            fields.append(("source_hashes", "{" + pairs + "}"))
    for r in (info.get("generated_from") or []) if args.subproject else ():
        if "subproject" in (cfg["registers"].get(r, {}).get("fields") or []):
            ids = [str(e.get("id", "?")) for e in pc.load_register(args.project, cfg, r) if e.get("subproject") == args.subproject]
            fields.append((f"entries_{r}", ", ".join(ids) or "none"))
    subs = cfg.get("subprojects")
    for sid, sp in (subs.items() if isinstance(subs, dict) else ()):  # render_views.py reports a malformed map
        parts = [f"{k}={sp[k]}" for k in ("kind", "stack", "docs_dir") if isinstance(sp, dict) and sp.get(k)]
        fields.append(("subproject", " ".join([str(sid), *parts])))
    for k, v in fields:
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
