#!/usr/bin/env python3
"""Fix duplicate ids after a merge.

Usage:
    python3 renumber.py [<ID>] [--line FILE:N] [--apply] [--rewrite FILE:N=NEW-ID]... [--keep FILE:N]... [--project ROOT]

Finds duplicate ids in registers, assigns the keeper and next free numbers for the prefix,
and lists ready-made flags for every reference in registers and draft documents.
Finished documents are left alone.
With --apply, rewrites confirmed references, moves changed entries to the end of their list,
and re-renders views.
Exit codes: 0 no duplicates or --apply succeeded, 1 dry run found duplicates or unreadable registers,
2 usage errors or unconfirmed references.
"""
import argparse
import contextlib
import io
import re
import shlex
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402


def field_contains_id(val, rx):
    """True when val (string, or strings in list/dict) matches regex rx."""
    if isinstance(val, str):
        return bool(rx.search(val))
    if isinstance(val, (list, tuple, set)):
        return any(field_contains_id(item, rx) for item in val)
    if isinstance(val, dict):
        return any(field_contains_id(v, rx) for v in val.values())
    return False


def get_label(entry):
    for k in ("title", "text", "name", "item"):
        val = entry.get(k)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def collect_duplicates(root, cfg, data):
    """Finds all duplicate ids across registers with an id field.
    Returns:
        dup_info: { id: { 'prefix': prefix, 'reg_name': reg_name, 'rel_file': rel_file,
                          'copies': [copy_dict], 'max_num': int } }
    """
    dup_info = {}
    reg_dir = cfg.get("paths", {}).get("registers", "pmo/registers")

    for reg_name, reg in cfg.get("registers", {}).items():
        fields = reg.get("fields") or []
        if "id" not in fields or reg_name not in data:
            continue
        prefix = reg.get("prefix")
        reg_file = reg.get("file", f"{reg_name}.yaml")
        rel_file = f"{reg_dir}/{reg_file}"
        fpath = Path(root) / rel_file
        if not fpath.exists():
            continue

        text = pc.read(fpath)
        elines = render_views.entry_lines(text)
        flines = text.splitlines()
        entries = data[reg_name]

        max_num = 0
        for e in entries:
            eid = e.get("id")
            if eid is not None:
                num = render_views._id_num(eid)
                if num > max_num:
                    max_num = num

        occurrences = {}
        for idx, e in enumerate(entries):
            eid = e.get("id")
            if eid is None or not isinstance(eid, (str, int)):
                continue
            eid_str = str(eid)
            lineno = elines[idx] if idx < len(elines) else None
            line_text = flines[lineno - 1] if lineno and lineno <= len(flines) else ""
            copy_dict = {
                "id": eid_str,
                "reg_name": reg_name,
                "rel_file": rel_file,
                "lineno": lineno,
                "entry": e,
                "line_text": line_text,
                "owner": e.get("owner"),
                "label": get_label(e),
                "pos": f"{rel_file}:{lineno}",
            }
            occurrences.setdefault(eid_str, []).append(copy_dict)

        for eid_str, copies in occurrences.items():
            if len(copies) > 1:
                dup_info[eid_str] = {
                    "prefix": prefix,
                    "reg_name": reg_name,
                    "rel_file": rel_file,
                    "copies": copies,
                    "max_num": max_num,
                }

    return dup_info


def collect_references(root, cfg, data, handled_dups):
    """Finds all references to duplicate ids in registers and documents.
    Returns:
        references_by_id: { id: { 'register_refs': [...], 'draft_refs': [...], 'finished_refs': [...] } }
        all_references: { pos: { 'old_id': id, 'new_ids': [...], 'type': 'register'|'draft' } }
    """
    references_by_id = {}
    all_references = {}
    reg_dir = cfg.get("paths", {}).get("registers", "pmo/registers")
    doc_dir = Path(root) / cfg.get("paths", {}).get("documents", "pmo/documents")

    for old_id, dinfo in handled_dups.items():
        rx = re.compile(r"(?<![A-Za-z0-9])" + re.escape(old_id) + r"(?![A-Za-z0-9])")
        copy_positions = {c["pos"] for c in dinfo["copies"]}
        new_ids = [c["new_id"] for c in dinfo["moving_copies"]]

        reg_refs = []
        for rname, reg in cfg.get("registers", {}).items():
            reg_file = reg.get("file", f"{rname}.yaml")
            rel_file = f"{reg_dir}/{reg_file}"
            fpath = Path(root) / rel_file
            if not fpath.exists():
                continue
            rtext = pc.read(fpath)
            rlines = rtext.splitlines()
            entries = data.get(rname, [])
            elines = render_views.entry_lines(rtext)

            for lidx, ltext in enumerate(rlines, 1):
                pos = f"{rel_file}:{lidx}"
                if pos in copy_positions:
                    continue
                if rx.search(ltext):
                    entry = {}
                    eid = None
                    elabel = None
                    matched_fields = []
                    if lidx in elines:
                        eidx = elines.index(lidx)
                        if eidx < len(entries):
                            entry = entries[eidx]
                            eid = entry.get("id")
                            elabel = get_label(entry)
                            for k, v in entry.items():
                                if field_contains_id(v, rx):
                                    matched_fields.append(k)

                    ref_dict = {
                        "pos": pos,
                        "entry_id": eid,
                        "label": elabel,
                        "fields": matched_fields,
                        "old_id": old_id,
                        "new_ids": new_ids,
                    }
                    reg_refs.append(ref_dict)
                    all_references[pos] = {
                        "old_id": old_id,
                        "new_ids": new_ids,
                        "type": "register",
                    }

        draft_refs = []
        finished_refs = []
        if doc_dir.is_dir():
            for dpath in sorted(doc_dir.rglob("*.md")):
                try:
                    rel_doc = str(dpath.relative_to(Path(root))).replace("\\", "/")
                except ValueError:
                    rel_doc = str(dpath).replace("\\", "/")
                dtext = pc.read(dpath)
                fm, _ = pc.split_front_matter(dtext)
                is_draft = isinstance(fm, dict) and fm.get("status") == "draft"

                for lidx, ltext in enumerate(dtext.splitlines(), 1):
                    pos = f"{rel_doc}:{lidx}"
                    if rx.search(ltext):
                        if is_draft:
                            ref_dict = {
                                "pos": pos,
                                "line_snippet": ltext.strip()[:100],
                                "old_id": old_id,
                                "new_ids": new_ids,
                            }
                            draft_refs.append(ref_dict)
                            all_references[pos] = {
                                "old_id": old_id,
                                "new_ids": new_ids,
                                "type": "draft",
                            }
                        else:
                            finished_refs.append(pos)

        references_by_id[old_id] = {
            "register_refs": reg_refs,
            "draft_refs": draft_refs,
            "finished_refs": finished_refs,
        }

    return references_by_id, all_references


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("id", nargs="?", default=None, metavar="ID", help="duplicate id to fix (default: all duplicate ids)")
    ap.add_argument("--line", default=None, metavar="FILE:N", help="line of the copy that keeps the id")
    ap.add_argument("--apply", action="store_true", help="apply the changes")
    ap.add_argument("--rewrite", action="append", default=[], metavar="FILE:N=NEW-ID", help="rewrite reference to new id")
    ap.add_argument("--keep", action="append", default=[], metavar="FILE:N", help="keep reference as old id")

    args = ap.parse_args(argv)

    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(args.project)
    if bad := render_views.config_errors(cfg, root=args.project):
        for err in bad:
            print("ERROR", err)
        return 2

    data, read_errors = render_views.read_registers(args.project, cfg)
    if read_errors:
        for err in read_errors:
            print("ERROR", err)
        return 1

    dup_info = collect_duplicates(args.project, cfg, data)

    if args.id is not None and args.id not in dup_info:
        print(f"ERROR id {args.id} is not duplicated", file=sys.stderr)
        return 2

    target_copy = None
    if args.line is not None:
        if ":" not in args.line or not args.line.rsplit(":", 1)[1].isdigit():
            print(f"ERROR invalid --line format: {args.line}", file=sys.stderr)
            return 2
        for d_id, dinfo in dup_info.items():
            for c in dinfo["copies"]:
                if c["pos"] == args.line:
                    target_copy = c
                    break
            if target_copy:
                break
        if not target_copy:
            print(f"ERROR line {args.line} holds no duplicate", file=sys.stderr)
            return 2
        if args.id is not None and target_copy["id"] != args.id:
            print(f"ERROR line {args.line} holds id {target_copy['id']}, not {args.id}", file=sys.stderr)
            return 2

    if not dup_info:
        print("no duplicate ids")
        return 0

    handled_dups = {}
    for d_id, dinfo in dup_info.items():
        if args.id is not None and d_id != args.id:
            continue
        if target_copy is not None and d_id != target_copy["id"]:
            continue

        copies = dinfo["copies"]
        if target_copy is not None and d_id == target_copy["id"]:
            keeper = target_copy
        else:
            keeper = copies[0]

        moving = [c for c in copies if c is not keeper]
        curr_num = dinfo["max_num"]
        prefix = dinfo["prefix"]
        for c in moving:
            curr_num += 1
            c["new_id"] = f"{prefix}-{curr_num}"
            c["old_id"] = d_id

        handled_dups[d_id] = {
            "prefix": prefix,
            "reg_name": dinfo["reg_name"],
            "rel_file": dinfo["rel_file"],
            "copies": copies,
            "keeper": keeper,
            "moving_copies": moving,
        }

    references_by_id, all_references = collect_references(args.project, cfg, data, handled_dups)

    if not args.apply:
        has_any_ref_needing_decision = False
        for d_id, dinfo in handled_dups.items():
            print(f"duplicate {d_id} in {dinfo['rel_file']}")

            keeper = dinfo["keeper"]
            k_owner = f"  owner {keeper['owner']}" if keeper["owner"] else ""
            k_label = f'  "{keeper["label"]}"' if keeper["label"] else ""
            print(f"  keeps {d_id}  {keeper['pos']}{k_label}{k_owner}")

            for c in dinfo["moving_copies"]:
                m_owner = f"  owner {c['owner']}" if c['owner'] else ""
                m_label = f'  "{c["label"]}"' if c["label"] else ""
                print(f"  gets  {c['new_id']}  {c['pos']}{m_label}{m_owner}")

            refs = references_by_id[d_id]
            reg_refs = refs["register_refs"]
            draft_refs = refs["draft_refs"]
            fin_refs = refs["finished_refs"]

            if reg_refs or draft_refs:
                has_any_ref_needing_decision = True
                print("  references:")
                for r in reg_refs:
                    qpos = shlex.quote(r["pos"])
                    desc_parts = []
                    if r["entry_id"]:
                        desc_parts.append(str(r["entry_id"]))
                    if r["label"]:
                        desc_parts.append(f'"{r["label"]}"')
                    desc = " ".join(desc_parts) if desc_parts else "entry"
                    fields_desc = f"in {', '.join(r['fields'])}" if r["fields"] else "in line"
                    print(f"    {qpos}  {desc}  {fields_desc}")
                    rewrites = ["--rewrite " + shlex.quote(r["pos"] + "=" + nid) for nid in r["new_ids"]]
                    print(f"      {'  |  '.join(rewrites)}  |  --keep {shlex.quote(r['pos'])}")

                for dr in draft_refs:
                    qpos = shlex.quote(dr["pos"])
                    print(f"    {qpos}  draft  {dr['line_snippet']}")
                    rewrites = ["--rewrite " + shlex.quote(dr["pos"] + "=" + nid) for nid in dr["new_ids"]]
                    print(f"      {'  |  '.join(rewrites)}  |  --keep {shlex.quote(dr['pos'])}")

            if fin_refs:
                print(f"  left alone (finished): {', '.join(fin_refs)}")

        if has_any_ref_needing_decision:
            print("next: choose --rewrite or --keep for each reference, then renumber.py --apply <flags>")
        else:
            print("next: renumber.py --apply")

        return 1

    decisions = {}
    for rw in args.rewrite:
        if "=" not in rw:
            print(f"ERROR invalid --rewrite format: {rw}", file=sys.stderr)
            return 2
        pos, new_id = rw.split("=", 1)
        if ":" not in pos or not pos.rsplit(":", 1)[1].isdigit() or not new_id:
            print(f"ERROR invalid --rewrite format: {rw}", file=sys.stderr)
            return 2
        if pos in decisions:
            print(f"ERROR multiple decisions for {pos}", file=sys.stderr)
            return 2
        decisions[pos] = ("rewrite", new_id)

    for k in args.keep:
        if ":" not in k or not k.rsplit(":", 1)[1].isdigit():
            print(f"ERROR invalid --keep format: {k}", file=sys.stderr)
            return 2
        if k in decisions:
            print(f"ERROR multiple decisions for {k}", file=sys.stderr)
            return 2
        decisions[k] = ("keep", None)

    for pos, (action, new_id) in decisions.items():
        if pos not in all_references:
            print(f"ERROR unknown reference line: {pos}", file=sys.stderr)
            return 2
        ref_info = all_references[pos]
        if action == "rewrite":
            if new_id not in ref_info["new_ids"]:
                print(f"ERROR {new_id} is not a valid new id for {pos}", file=sys.stderr)
                return 2

    for pos in all_references:
        if pos not in decisions:
            print(f"ERROR reference {pos} has no decision", file=sys.stderr)
            return 2

    files_to_edit = set()
    for d_id, dinfo in handled_dups.items():
        files_to_edit.add(dinfo["rel_file"])
    for pos, (action, _) in decisions.items():
        if action == "rewrite":
            f_rel = pos.rsplit(":", 1)[0]
            files_to_edit.add(f_rel)

    changed_lines = []

    for rel_file in sorted(files_to_edit):
        fpath = Path(args.project) / rel_file
        orig_text = pc.read(fpath)
        orig_lines = orig_text.splitlines()

        moving_copies_for_file = []
        for d_id, dinfo in handled_dups.items():
            if dinfo["rel_file"] == rel_file:
                moving_copies_for_file.extend(dinfo["moving_copies"])

        moving_by_lineno = {c["lineno"]: c for c in moving_copies_for_file}

        rewrites_for_file = {}
        for pos, (action, new_id) in decisions.items():
            if action == "rewrite":
                rf, lstr = pos.rsplit(":", 1)
                if rf == rel_file:
                    rewrites_for_file[int(lstr)] = (all_references[pos]["old_id"], new_id)

        newlines = []
        for idx, line in enumerate(orig_lines, 1):
            if idx in rewrites_for_file:
                old_id, new_id = rewrites_for_file[idx]
                rx = re.compile(r"(?<![A-Za-z0-9])" + re.escape(old_id) + r"(?![A-Za-z0-9])")
                newlines.append(rx.sub(new_id, line))
            else:
                newlines.append(line)

        final_lines = []
        changed_in_this_file = []

        if moving_copies_for_file:
            moving_linenos = set(moving_by_lineno.keys())
            elines = render_views.entry_lines(orig_text)
            rem_elines = [l for l in elines if l not in moving_linenos]
            insert_after = rem_elines[-1] if rem_elines else (elines[-1] if elines else len(orig_lines))

            modified_moving_lines = []
            for c in moving_copies_for_file:
                c_lineno = c["lineno"]
                old_id = c["old_id"]
                new_id = c["new_id"]
                raw_line = newlines[c_lineno - 1]
                mod_line = re.sub(r"id:\s*" + re.escape(old_id) + r"(?=[,}\s])", f"id: {new_id}", raw_line, count=1)
                modified_moving_lines.append(mod_line)

            for idx, line in enumerate(newlines, 1):
                if idx in moving_linenos:
                    continue
                final_lines.append(line)
                if idx in rewrites_for_file:
                    changed_in_this_file.append((rel_file, len(final_lines), line))
                if idx == insert_after:
                    for mod_line in modified_moving_lines:
                        final_lines.append(mod_line)
                        changed_in_this_file.append((rel_file, len(final_lines), mod_line))

            if insert_after == 0 or insert_after not in range(1, len(newlines) + 1):
                for mod_line in modified_moving_lines:
                    final_lines.append(mod_line)
                    changed_in_this_file.append((rel_file, len(final_lines), mod_line))
        else:
            for idx, line in enumerate(newlines, 1):
                final_lines.append(line)
                if idx in rewrites_for_file:
                    changed_in_this_file.append((rel_file, len(final_lines), line))

        new_content = "\n".join(final_lines) + "\n"
        pc.write(fpath, new_content)
        changed_lines.extend(changed_in_this_file)

    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            rv_code = render_views.main(["--project", str(args.project)])
    except SystemExit as e:
        rv_code = e.code or 0
        if isinstance(rv_code, str):
            out.write(rv_code + "\n")
            rv_code = 1
    rv_out = out.getvalue()
    if rv_out:
        sys.stdout.write(rv_out)

    if rv_code != 0:
        print("registers were changed and views were not written")
        return 1

    for rel_file, lineno, line in changed_lines:
        print(f"changed: {rel_file}:{lineno}  {line.strip()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
