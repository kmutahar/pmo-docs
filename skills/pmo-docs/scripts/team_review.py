#!/usr/bin/env python3
"""A review checklist per person, from the registers. Prints Markdown, or CSV with --csv.

Usage:
    python3 team_review.py [--project ROOT] [--csv] [--lang CODE]
    python3 team_review.py [--project ROOT] --import FILE.csv

For each roster person, lists the open entries they own in tasks, risks, issues, actions and
requirements ("open" means the status is not one of the register's `closed` statuses in the config).
Each translation language's glossary rows under Proposed are listed for the project manager
(`project.manager`), who moves them to Approved. Entries with no owner, or an owner who is not on
the roster, get their own heading, so nothing is dropped. Markdown is a `- [ ]` checklist per
person; --csv prints one row per entry: person, register, id, title, status, due (blank when the
register has no due date), description, question. A missing register counts as empty; a missing glossary file is skipped.
The description is the entry's optional `description` field and the question its optional `question` field. With
--lang CODE (a translation language) both come from that language's names file (`approved`, then `proposed`:
register -> id -> field -> text) when it has them; the entry's own text is the fallback, and a translated title
stands in for a missing description. Nothing is invented.
--import FILE.csv reads a CSV like the one --csv prints, plus an `answer` and/or `done` column a reviewer filled in
(`done` is x, yes, true or 1). It prints the proposed changes (register, id, current status, proposed status, answer)
and writes nothing; unknown ids and ids already at the proposed status are listed apart, with counts. The status
for done is the first of `registers.<name>.done`, else the first of `closed`.
Exit codes: 0 report printed, 2 usage error, missing project folder, a missing or unreadable import file, or a register that is not valid YAML.
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


def load_names(root, cfg, lang):
    """The language's names file as a dict ({} without --lang, a file or valid YAML)."""
    rel = pc.names_path(cfg, lang) if lang else None
    f = Path(root) / rel if rel else None
    if not f or not f.is_file():
        return {}
    try:
        data = pc.load_yaml(pc.read(f))
    except pc.yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def translated(names, reg, eid, field):
    """Text of one field from the names file (`approved` first, then `proposed`), or None."""
    for sec in ("approved", "proposed"):
        regs = names.get(sec)
        ids = regs.get(reg) if isinstance(regs, dict) else None
        fields = ids.get(eid) if isinstance(ids, dict) else None
        text = fields.get(field) if isinstance(fields, dict) else None
        if isinstance(text, str) and text.strip():
            return text
    return None


def collect(root, cfg, lang=None):
    """{person: [(register, id, title, status, due, description, question)]}: roster order first, then other owners by name."""
    names = pc.roster_names(root, cfg)
    tnames = load_names(root, cfg, lang)
    people = {n: [] for n in names.values()}
    for reg in REGISTERS:
        for e in overdue.open_entries(root, cfg, reg):
            eid = e.get("id")
            desc = (translated(tnames, reg, eid, "description") or e.get("description")
                    or translated(tnames, reg, eid, "title") or translated(tnames, reg, eid, "text"))
            question = translated(tnames, reg, eid, "question") or e.get("question")
            row = (reg, eid, e.get("title") or e.get("text"), e.get("status"), e["_due"] or e["_bad"], desc, question)
            people.setdefault(pc.person(e.get("owner"), names), []).append(row)
    manager = pc.person((cfg.get("project") or {}).get("manager"), names)
    for lang in pc.languages(cfg)["translations"]:
        for gid, term in proposed_terms(root, cfg, lang):
            people.setdefault(manager, []).append((f"glossary-{lang}", gid, term, "proposed", None, None, None))
    roster = list(names.values())
    return {n: people[n] for n in roster + sorted(set(people) - set(roster))}


def markdown(people):
    out = ["# Team review\n"]
    for name, rows in people.items():
        out.append(f"## {pc.inline(name)} ({len(rows)})\n")
        out.append("\n".join(
            f"- [ ] `{pc.inline(i)}` {pc.inline(t or 'not recorded')} ({reg}, {pc.inline(s or 'not recorded')}"
            + (f", due {pc.inline(d)}" if d else "") + ")" + (f" - {pc.inline(desc)}" if desc else "")
            + (f"\n  - Question: {pc.inline(q)}" if q else "")
            for reg, i, t, s, d, desc, q in rows) or "- None")
        out.append("")
    return "\n".join(out)


def csv_text(people):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["person", "register", "id", "title", "status", "due", "description", "question"])
    for name, rows in people.items():
        w.writerows([name, *row] for row in rows)
    return buf.getvalue()


def done_status(cfg, reg):
    """The status that means done for a register: the first of `done`, else the first of `closed`; None without one."""
    return next(iter(pc.statuses(cfg, reg, "done") or pc.statuses(cfg, reg, "closed")), None)


def proposals(root, cfg, rows):
    """Compare the reviewer's CSV rows with the registers. Returns lists: change, answer, same, unknown, skipped, none."""
    out = {k: [] for k in ("change", "answer", "same", "unknown", "skipped", "none")}
    cache = {}
    for r in rows:
        reg, eid = (r.get("register") or "").strip(), (r.get("id") or "").strip()
        answer = (r.get("answer") or "").strip()
        done = (r.get("done") or "").strip().lower() in ("x", "yes", "true", "1")
        if not done and not answer:
            out["none"].append((reg, eid))
        elif reg not in REGISTERS:
            out["skipped"].append((reg, eid))
        else:
            if reg not in cache:
                cache[reg] = {str(e.get("id")): e for e in pc.load_register(root, cfg, reg) if isinstance(e, dict)}
            entry = cache[reg].get(eid)
            cur, new = (entry or {}).get("status"), done_status(cfg, reg) if done else None
            if entry is None:
                out["unknown"].append((reg, eid))
            elif done and new is None:
                out["skipped"].append((reg, eid))
            elif done and cur == new:
                out["same"].append((reg, eid, cur, new, answer))
            else:
                out["change" if done else "answer"].append((reg, eid, cur, new or cur, answer))
    return out


def import_text(p):
    def line(t):
        reg, eid, *rest = t
        s = f"- `{pc.inline(eid)}` ({reg})"
        if rest:
            s += f": {pc.inline(rest[0] or 'not recorded')} -> {pc.inline(rest[1] or 'not recorded')}"
            s += f"; answer: {pc.inline(rest[2])}" if rest[2] else ""
        return s
    out = ["# Proposed changes (nothing was written)\n"]
    for key, head in (("change", "Status changes"), ("answer", "Answers only (status unchanged)"),
                      ("same", "Already at the proposed status"), ("unknown", "Unknown ids"),
                      ("skipped", "Skipped (not a register with a done status)"), ("none", "No answer and not done")):
        out.append(f"## {head} ({len(p[key])})\n")
        out.append("\n".join(line(t) for t in p[key]) or "- None")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("--csv", action="store_true", help="print CSV (one row per entry) instead of Markdown")
    ap.add_argument("--lang", metavar="CODE", help="show description and question from this translation language's names file")
    ap.add_argument("--import", dest="import_file", metavar="FILE.csv",
                    help="print the changes a reviewer's CSV proposes (register, id, current and proposed status, answer); writes nothing")
    args = ap.parse_args(argv)
    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")
    if args.import_file and (args.csv or args.lang):
        ap.error("--import cannot be combined with --csv or --lang")
    try:
        cfg = pc.load_config(args.project)
        if args.lang and args.lang not in pc.languages(cfg)["translations"]:
            ap.error(f"--lang {args.lang}: not a translation language in the config")
        if args.import_file:
            try:
                rows = list(csv.DictReader(io.StringIO(pc.read(args.import_file))))
            except (OSError, UnicodeDecodeError, csv.Error) as e:
                ap.error(f"cannot read {args.import_file}: {e}")
            if not rows or not {"register", "id"} <= set(rows[0]):
                ap.error(f"{args.import_file}: needs a header row with `register` and `id` columns and at least one row")
            sys.stdout.write(import_text(proposals(args.project, cfg, rows)))
            return 0
        people = collect(args.project, cfg, args.lang)
    except (pc.yaml.YAMLError, AttributeError, ValueError) as e:  # a register that is not `name:` plus a list of maps
        print(f"ERROR a register is not readable ({str(e).splitlines()[0]}); run render_views.py to see which", file=sys.stderr)
        return 2
    sys.stdout.write(csv_text(people) if args.csv else markdown(people))
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
