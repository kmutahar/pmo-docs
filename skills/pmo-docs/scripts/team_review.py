#!/usr/bin/env python3
"""A review checklist per person, from the registers. Prints Markdown, or CSV with --csv.

Usage:
    python3 team_review.py [--project ROOT] [--csv]

For each roster person, lists the open entries they own in tasks, risks, issues, actions and
requirements ("open" means the status is not one of the register's `closed` statuses in the config).
Each translation language's glossary rows under Proposed are listed for the project manager
(`project.manager`), who moves them to Approved. Entries with no owner, or an owner who is not on
the roster, get their own heading, so nothing is dropped. Markdown is a `- [ ]` checklist per
person; --csv prints one row per entry: person, register, id, title, status, due (blank when the
register has no due date). A missing register counts as empty; a missing glossary file is skipped.
Exit codes: 0 report printed, 2 usage error, missing project folder or a register that is not valid YAML.
"""
import argparse
import csv
import io
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import overdue  # noqa: E402
import pmo_common as pc  # noqa: E402

REGISTERS = ("tasks", "risks", "issues", "actions", "requirements")


def proposed_terms(root, cfg, lang):
    """(ID, term and translation) of each row under `## Proposed` in the language's glossary file."""
    rel = pc.glossary_path(cfg, lang)
    f = Path(root) / rel if rel else None
    if not f or not f.is_file():
        return []
    rows, inside = [], False
    for ln in pc.read(f).splitlines():
        if ln.startswith("## "):
            inside = ln[3:].strip().lower() == "proposed"
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if inside and re.fullmatch(r"G-\d+", cells[0]) and len(cells) > 2:
            rows.append((cells[0], " -> ".join(c for c in cells[1:3] if c)))
    return rows


def collect(root, cfg):
    """{person: [(register, id, title, status, due)]}: roster order first, then other owners by name."""
    names = pc.roster_names(root, cfg)
    people = {n: [] for n in names.values()}
    for reg in REGISTERS:
        for e in overdue.open_entries(root, cfg, reg):
            row = (reg, e.get("id"), e.get("title") or e.get("text"), e.get("status"), e["_due"] or e["_bad"])
            people.setdefault(pc.person(e.get("owner"), names), []).append(row)
    manager = pc.person((cfg.get("project") or {}).get("manager"), names)
    for lang in pc.languages(cfg)["translations"]:
        for gid, term in proposed_terms(root, cfg, lang):
            people.setdefault(manager, []).append((f"glossary-{lang}", gid, term, "proposed", None))
    roster = list(names.values())
    return {n: people[n] for n in roster + sorted(set(people) - set(roster))}


def markdown(people):
    out = ["# Team review\n"]
    for name, rows in people.items():
        out.append(f"## {pc.inline(name)} ({len(rows)})\n")
        out.append("\n".join(
            f"- [ ] `{pc.inline(i)}` {pc.inline(t or 'not recorded')} ({reg}, {pc.inline(s or 'not recorded')}"
            + (f", due {pc.inline(d)}" if d else "") + ")"
            for reg, i, t, s, d in rows) or "- None")
        out.append("")
    return "\n".join(out)


def csv_text(people):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["person", "register", "id", "title", "status", "due"])
    for name, rows in people.items():
        w.writerows([name, reg, i, t, s, d] for reg, i, t, s, d in rows)
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("--csv", action="store_true", help="print CSV (one row per entry) instead of Markdown")
    args = ap.parse_args(argv)
    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")
    try:
        people = collect(args.project, pc.load_config(args.project))
    except (pc.yaml.YAMLError, AttributeError, ValueError) as e:  # a register that is not `name:` plus a list of maps
        print(f"ERROR a register is not readable ({str(e).splitlines()[0]}); run render_views.py to see which", file=sys.stderr)
        return 2
    sys.stdout.write(csv_text(people) if args.csv else markdown(people))
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
