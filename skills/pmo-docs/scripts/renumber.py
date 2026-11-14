#!/usr/bin/env python3
"""Fix duplicate ids after a merge.

Usage:
    python3 renumber.py [<ID>] [--line FILE:N] [--apply] [--rewrite FILE:N=NEW-ID]... [--keep FILE:N[=OLD-ID]]... [--project ROOT]

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

sys.dont_write_bytecode = True
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
        flines = text.split("\n")
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
        all_references: { (pos, old_id): { 'old_id': id, 'new_ids': [...], 'type': 'register'|'draft' } }
    """
    references_by_id = {}
    all_references = {}
    reg_dir = cfg.get("paths", {}).get("registers", "pmo/registers")
    doc_dir = Path(root) / cfg.get("paths", {}).get("documents", "pmo/documents")

    valid_docs = []
    if doc_dir.is_dir():
        for dpath in sorted(doc_dir.rglob("*.md")):
            if not dpath.is_file():
                continue
            try:
                rel_doc = str(dpath.relative_to(Path(root))).replace("\\", "/")
            except ValueError:
                rel_doc = str(dpath).replace("\\", "/")
            if pc.outside(root, rel_doc):
                print(f"skipped (outside the project): {rel_doc}")
                continue
            try:
                dtext = pc.read(dpath)
            except UnicodeDecodeError:
                print(f"skipped (not UTF-8 text): {rel_doc}")
                continue
            fm, _ = pc.split_front_matter(dtext)
            is_draft = isinstance(fm, dict) and fm.get("status") == "draft"
            valid_docs.append((rel_doc, dtext, is_draft))

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
            rlines = rtext.split("\n")
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
                    all_references[(pos, old_id)] = {
                        "old_id": old_id,
                        "new_ids": new_ids,
                        "type": "register",
                    }

        draft_refs = []
        finished_refs = []
        for rel_doc, dtext, is_draft in valid_docs:
            for lidx, ltext in enumerate(dtext.split("\n"), 1):
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
                        all_references[(pos, old_id)] = {
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
    ap.add_argument("--keep", action="append", default=[], metavar="FILE:N[=OLD-ID]", help="keep reference as old id (name OLD-ID if line mentions several)")

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
    next_num = {}
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
        reg_name = dinfo["reg_name"]
        curr = max(next_num.get(reg_name, 0), dinfo["max_num"])
        prefix = dinfo["prefix"]
        width = len(d_id.rsplit("-", 1)[1]) if "-" in d_id else 1
        for c in moving:
            curr += 1
            num_str = str(curr).zfill(width)
            c["new_id"] = f"{prefix}-{num_str}" if prefix else num_str
            c["old_id"] = d_id
        next_num[reg_name] = curr

        handled_dups[d_id] = {
            "prefix": prefix,
            "reg_name": reg_name,
            "rel_file": dinfo["rel_file"],
            "copies": copies,
            "keeper": keeper,
            "moving_copies": moving,
        }

    references_by_id, all_references = collect_references(args.project, cfg, data, handled_dups)
    ids_at = {}
    for pos, old_id in all_references:
        ids_at.setdefault(pos, set()).add(old_id)

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
                    if len(ids_at[r["pos"]]) > 1:
                        keep_flag = "--keep " + shlex.quote(r["pos"] + "=" + d_id)
                    else:
                        keep_flag = "--keep " + shlex.quote(r["pos"])
                    print(f"      {'  |  '.join(rewrites)}  |  {keep_flag}")

                for dr in draft_refs:
                    qpos = shlex.quote(dr["pos"])
                    print(f"    {qpos}  draft  {dr['line_snippet']}")
                    rewrites = ["--rewrite " + shlex.quote(dr["pos"] + "=" + nid) for nid in dr["new_ids"]]
                    if len(ids_at[dr["pos"]]) > 1:
                        keep_flag = "--keep " + shlex.quote(dr["pos"] + "=" + d_id)
                    else:
                        keep_flag = "--keep " + shlex.quote(dr["pos"])
                    print(f"      {'  |  '.join(rewrites)}  |  {keep_flag}")

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
        if pos not in ids_at:
            print(f"ERROR unknown reference line: {pos}", file=sys.stderr)
            return 2
        matched_old_id = None
        for (p, o_id), rinfo in all_references.items():
            if p == pos and new_id in rinfo["new_ids"]:
                matched_old_id = o_id
                break
        if matched_old_id is None:
            print(f"ERROR {new_id} is not a valid new id for {pos}", file=sys.stderr)
            return 2
        key = (pos, matched_old_id)
        if key in decisions:
            print(f"ERROR multiple decisions for {pos}", file=sys.stderr)
            return 2
        decisions[key] = ("rewrite", new_id)

    for k in args.keep:
        if "=" in k:
            pos, old_id = k.split("=", 1)
            if ":" not in pos or not pos.rsplit(":", 1)[1].isdigit() or not old_id:
                print(f"ERROR invalid --keep format: {k}", file=sys.stderr)
                return 2
            if pos not in ids_at:
                print(f"ERROR unknown reference line: {pos}", file=sys.stderr)
                return 2
            if (pos, old_id) not in all_references:
                print(f"ERROR {old_id} is not a valid id for {pos}", file=sys.stderr)
                return 2
        else:
            pos = k
            if ":" not in pos or not pos.rsplit(":", 1)[1].isdigit():
                print(f"ERROR invalid --keep format: {k}", file=sys.stderr)
                return 2
            if pos not in ids_at:
                print(f"ERROR unknown reference line: {pos}", file=sys.stderr)
                return 2
            if len(ids_at[pos]) > 1:
                print(f"ERROR reference {pos} mentions several duplicated ids; use --keep {pos}=OLD-ID", file=sys.stderr)
                return 2
            old_id = next(iter(ids_at[pos]))

        key = (pos, old_id)
        if key in decisions:
            print(f"ERROR multiple decisions for {pos}", file=sys.stderr)
            return 2
        decisions[key] = ("keep", None)

    for (pos, old_id) in all_references:
        if (pos, old_id) not in decisions:
            if len(ids_at[pos]) > 1:
                print(f"ERROR reference {pos} has no decision for {old_id}", file=sys.stderr)
            else:
                print(f"ERROR reference {pos} has no decision", file=sys.stderr)
            return 2

    files_to_edit = set()
    for d_id, dinfo in handled_dups.items():
        files_to_edit.add(dinfo["rel_file"])
    for (pos, old_id), (action, _) in decisions.items():
        if action == "rewrite":
            f_rel = pos.rsplit(":", 1)[0]
            files_to_edit.add(f_rel)

    # shortcut: a lone CR line ending is read as a line break by pc.read, so line numbers can differ for such a file; upgrade when one turns up
    pending = {}
    all_changed_lines = []

    for rel_file in sorted(files_to_edit):
        fpath = Path(args.project) / rel_file
        orig_text = open(fpath, encoding="utf-8", newline="").read()
        orig_lines = orig_text.split("\n")

        moving_copies_for_file = []
        for d_id, dinfo in handled_dups.items():
            if dinfo["rel_file"] == rel_file:
                moving_copies_for_file.extend(dinfo["moving_copies"])

        moving_by_lineno = {c["lineno"]: c for c in moving_copies_for_file}

        rewrites_for_file = {}
        for (pos, old_id), (action, new_id) in decisions.items():
            if action == "rewrite":
                rf, lstr = pos.rsplit(":", 1)
                if rf == rel_file:
                    rewrites_for_file.setdefault(int(lstr), []).append((old_id, new_id))

        newlines = []
        for idx, line in enumerate(orig_lines, 1):
            if idx in rewrites_for_file:
                mod_line = line
                for old_id, new_id in rewrites_for_file[idx]:
                    rx = re.compile(r"(?<![A-Za-z0-9])" + re.escape(old_id) + r"(?![A-Za-z0-9])")
                    mod_line = rx.sub(new_id, mod_line)
                newlines.append(mod_line)
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

                pattern = r'(?<![A-Za-z0-9_])id:\s*(["\']?)' + re.escape(old_id) + r'\1(?=\s*[,}])'
                def make_repl(nid):
                    def repl_id(m):
                        quote = m.group(1)
                        return "id: " + quote + nid + quote
                    return repl_id

                mod_line = re.sub(pattern, make_repl(new_id), raw_line, count=1)

                ok = False
                try:
                    lstripped = mod_line.lstrip()
                    if lstripped.startswith("- "):
                        parsed = pc.yaml.safe_load(lstripped[2:])
                        if isinstance(parsed, dict) and parsed.get("id") == new_id:
                            ok = True
                except Exception:
                    ok = False

                if not ok:
                    print(f"ERROR cannot rename the id on {c['pos']}", file=sys.stderr)
                    return 2

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

        new_content = "\n".join(final_lines)
        pending[rel_file] = new_content
        all_changed_lines.extend(changed_in_this_file)

    for rel_file in sorted(pending):
        pc.safe_write(args.project, rel_file, pending[rel_file])

    for rel_file, lineno, line in all_changed_lines:
        print(f"changed: {rel_file}:{lineno}  {line.strip()}")

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
        if "duplicate id" in rv_out:
            print("next: renumber.py")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
