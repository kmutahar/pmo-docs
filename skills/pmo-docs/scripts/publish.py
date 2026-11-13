#!/usr/bin/env python3
"""Publish finished documents to a target folder or repo.

Usage:
    python3 publish.py [--apply] [--overwrite REL]... [--include REL]... [--as-of YYYY-MM-DD] [--project ROOT]

Exit codes:
    0 success, or mode is none, or dry run clean
    1 conflict or stale document left uncopied during --apply, or an invalid document
    2 usage, config error, path outside project, unknown REL, or a file that could not be copied
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_audit  # noqa: E402
import pmo_common as pc  # noqa: E402
import structure_check  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Publish finished documents to a target folder or repo.")
    pc.add_project_arg(ap)
    ap.add_argument("--apply", action="store_true", help="perform the copy; without this flag, print a dry-run listing")
    ap.add_argument("--overwrite", action="append", default=[], metavar="REL", help="overwrite a conflicting document")
    ap.add_argument("--include", action="append", default=[], metavar="REL", help="publish a stale document")
    ap.add_argument("--as-of", type=datetime.date.fromisoformat, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date for staleness checks (default: today)")
    args = ap.parse_args(argv)

    root = Path(args.project).resolve()
    if not root.is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(root)
    pub = cfg.get("publish") or {}
    if not isinstance(pub, dict):
        print("ERROR publish must be a map with mode, path and url", file=sys.stderr)
        return 2
    mode = pub.get("mode", "none")

    if mode == "none":
        print("publish mode is none: set publish.mode and publish.path in pmo/config.yaml")
        return 0

    if mode not in ("folder", "repo"):
        print(f"ERROR invalid publish mode: {mode!r}", file=sys.stderr)
        return 2

    raw_path = pub.get("path")
    if not raw_path or not isinstance(raw_path, str) or not raw_path.strip():
        print("ERROR publish.path must be a non-empty string", file=sys.stderr)
        return 2

    # Validate target directory
    if mode == "folder":
        if pc.outside(root, raw_path):
            print(f"ERROR publish.path {raw_path!r} must be inside the project and not inside .git", file=sys.stderr)
            return 2
        target_dir = (root / raw_path).resolve()
        docs_dir = (root / cfg["paths"]["documents"]).resolve()
        if target_dir == docs_dir or target_dir in docs_dir.parents or docs_dir in target_dir.parents:
            print(f"ERROR publish.path cannot be or contain paths.documents ({cfg['paths']['documents']})", file=sys.stderr)
            return 2
    else:  # repo
        target_dir = Path(raw_path)
        if not target_dir.is_absolute():
            target_dir = (root / target_dir)
        target_dir = target_dir.resolve()
        if not target_dir.is_dir():
            print(f"ERROR repo folder not found: {raw_path}", file=sys.stderr)
            return 2

        try:
            res = subprocess.run(["git", "-C", str(target_dir), "rev-parse", "--show-toplevel"],
                                 capture_output=True, text=True, encoding="utf-8")
        except OSError as e:
            print(f"ERROR cannot run git: {e}", file=sys.stderr)
            return 2
        if res.returncode != 0:
            print(f"ERROR {raw_path} is not a git repository", file=sys.stderr)
            return 2
        repo_top = Path(res.stdout.strip()).resolve()
        if repo_top != target_dir:
            print(f"ERROR {raw_path} is not the top level of a git repository", file=sys.stderr)
            return 2

        res_proj = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                                  capture_output=True, text=True, encoding="utf-8")
        if res_proj.returncode == 0:
            proj_top = Path(res_proj.stdout.strip()).resolve()
            if proj_top == repo_top:
                print("ERROR publish.path cannot be the project repository itself", file=sys.stderr)
                return 2

    # Candidates scan
    docs_base = root / cfg["paths"]["documents"]
    files = sorted(docs_base.rglob("*.md")) if docs_base.exists() else []

    doc_types = cfg.get("doc_types", {})
    candidates = []
    drafts_count = 0
    excluded_count = 0

    for f in files:
        rel = f.relative_to(docs_base).as_posix()
        try:
            fm = pc.split_front_matter(pc.read(f))[0] or {}
        except UnicodeDecodeError:  # not UTF-8: not a document we can publish
            fm = {}
        ty = fm.get("type")
        if not isinstance(ty, str):
            ty = None
        st = fm.get("status")

        if ty in doc_types and doc_types[ty].get("publish") is False:
            excluded_count += 1
            continue

        if st != "finished":
            drafts_count += 1
            continue

        if not ty or ty not in doc_types:
            continue

        candidates.append((rel, f))

    # Classify candidates
    classified = []
    for rel, f in candidates:
        target_f = target_dir / rel
        try:
            target_f.resolve().relative_to(target_dir)
        except ValueError:
            print(f"ERROR target path for {rel!r} escapes publish directory", file=sys.stderr)
            return 2

        text = pc.read(f)
        errors, _ = structure_check.check(root, cfg, text)
        if errors:
            classified.append((rel, f, "invalid", errors))
            continue

        audit_findings = docs_audit.audit_file(root, cfg, f, docs_base, args.as_of)
        is_stale = any(chk in docs_audit.STALE_CHECKS for chk, _ in audit_findings)

        if not target_f.exists():
            state = "stale" if is_stale else "new"
        elif target_f.read_bytes() == f.read_bytes():
            state = "unchanged"
        else:
            state = "stale, conflict" if is_stale else "conflict"

        classified.append((rel, f, state, []))

    # Validate flag arguments (dry run too)
    cand_rels = {rel for rel, _, _, _ in classified}
    for r in args.overwrite:
        if r not in cand_rels:
            print(f"ERROR --overwrite {r!r} is not a candidate document", file=sys.stderr)
            return 2
    for r in args.include:
        if r not in cand_rels:
            print(f"ERROR --include {r!r} is not a candidate document", file=sys.stderr)
            return 2

    # Dry-run listing
    if not args.apply:
        url_base = pub.get("url")
        for rel, _, state, errors in classified:
            print(f"{state}: {rel}")
            if state == "invalid":
                for err in errors[:3]:
                    print(f"  {err}")
                if len(errors) > 3:
                    print(f"  ... and {len(errors) - 3} more")
            elif state == "new" and url_base:
                clean_url = str(url_base).rstrip("/")
                print(f"url: {clean_url}/{urllib.parse.quote(rel)}")
        print(f"drafts: {drafts_count}")
        print(f"excluded: {excluded_count}")
        return 1 if any(st == "invalid" for _, _, st, _ in classified) else 0

    # Apply copies
    overwrite_set = set(args.overwrite)
    include_set = set(args.include)
    uncopied_issue = False

    for rel, src_f, state, _ in classified:
        target_f = target_dir / rel
        to_copy = False

        if state == "unchanged":
            continue
        elif state == "new":
            to_copy = True
        elif state == "invalid":
            to_copy = False
        else:
            stale = state in ("stale", "stale, conflict")
            conflict = state in ("conflict", "stale, conflict")
            if (not stale or rel in include_set) and (not conflict or rel in overwrite_set):
                to_copy = True
            else:
                to_copy = False

        if to_copy:
            tmp_f = target_f.with_name(target_f.name + ".tmp")
            try:
                target_f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_f, tmp_f)
                os.replace(tmp_f, target_f)  # a target is never left half written
            except OSError as e:
                try:
                    tmp_f.unlink(missing_ok=True)
                except OSError:  # the target folder itself is unusable (for example a file): report the copy error
                    pass
                print(f"ERROR cannot copy {rel!r} to {target_f}: {e}", file=sys.stderr)
                return 2
            print(f"copied: {rel}")
        else:
            uncopied_issue = True
            if state == "invalid":
                print(f"uncopied: {rel} (invalid: fix the errors listed by structure_check.py)")
            else:
                stale = state in ("stale", "stale, conflict")
                conflict = state in ("conflict", "stale, conflict")
                reasons = []
                needed_flags = []
                if stale and rel not in include_set:
                    reasons.append("stale")
                    needed_flags.append(f"--include {rel}")
                if conflict and rel not in overwrite_set:
                    reasons.append("conflict")
                    needed_flags.append(f"--overwrite {rel}")
                state_str = ", ".join(reasons)
                flags_str = " and ".join(needed_flags)
                print(f"uncopied: {rel} ({state_str}: pass {flags_str})")

    return 1 if uncopied_issue else 0


if __name__ == "__main__":
    sys.exit(main())
