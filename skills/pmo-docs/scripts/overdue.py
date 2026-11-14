#!/usr/bin/env python3
"""Overdue work, from the registers. Prints Markdown tables.

Usage:
    python3 overdue.py [--project ROOT] [--as-of YYYY-MM-DD] [--days N]

Lists open tasks and actions whose due date is before the as-of date, milestones that are
overdue or due within N days inclusive (default 14), open issues by severity and open risks.
"Open" means the entry's status is not one of the register's `closed` statuses in the config.
Tasks are sorted by days late, then by vocab.priority_order. Issues are sorted most severe first:
the vocab named by the issues register's `severity` enum is listed least severe first, so it is
read from the end. An entry whose `due` is not a date gets a row under "Bad due dates". A
missing register counts as empty.
Exit codes: 0 report printed, 2 usage error, missing project folder or a register that is not valid YAML.
"""
import argparse
import datetime
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402


def table(head, rows):
    return pc.md_table(head, [["not set" if c is None else c for c in r] for r in rows])


def open_entries(root, cfg, name):
    """Entries of a register whose status is not closed, each with a parsed `_due` (None when unset or bad)
    and `_bad` (the raw value of a due date that does not parse, else None)."""
    closed = cfg["registers"].get(name, {}).get("closed", [])
    out = []
    for e in pc.load_register(root, cfg, name):
        if e.get("status") in closed:
            continue
        try:
            due, bad = pc.to_date(e.get("due")), None
        except ValueError:
            due, bad = None, e.get("due")
        out.append({**e, "_due": due, "_bad": bad})
    return out


def report(root, cfg, as_of, days):
    order = cfg["vocab"].get("priority_order") or []
    prio = lambda t: order.index(t["priority"]) if t.get("priority") in order else len(order)  # noqa: E731
    by_id = lambda e: (pc.id_num(e.get("id")), str(e.get("id")))  # noqa: E731
    tasks, acts, ms = (open_entries(root, cfg, n) for n in ("tasks", "actions", "milestones"))
    bad = [(n, e.get("id"), e["_bad"]) for n, es in (("tasks", tasks), ("actions", acts), ("milestones", ms)) for e in es if e["_bad"] is not None]
    tasks = sorted((t for t in tasks if t["_due"] and t["_due"] < as_of), key=lambda t: (t["_due"], prio(t), by_id(t)))
    acts = sorted((a for a in acts if a["_due"] and a["_due"] < as_of), key=lambda a: (a["_due"], by_id(a)))
    limit = as_of + datetime.timedelta(days=days)
    ms = sorted((m for m in ms if m["_due"] and m["_due"] <= limit), key=lambda m: (m["_due"], by_id(m)))
    sev_vocab = cfg["registers"].get("issues", {}).get("enums", {}).get("severity")
    sev = list(reversed(cfg["vocab"].get(sev_vocab) or []))  # vocab is least severe first
    issues = sorted(open_entries(root, cfg, "issues"),
                    key=lambda i: (sev.index(i.get("severity")) if i.get("severity") in sev else len(sev), by_id(i)))
    risks = sorted(open_entries(root, cfg, "risks"), key=by_id)
    out = [
        f"# Overdue - as of {as_of}\n",
        f"Overdue tasks: {len(tasks)}, open actions past due: {len(acts)}, milestones due within {days} days or overdue: {len(ms)}, "
        f"open issues: {len(issues)}, open risks: {len(risks)}\n",
        "## Overdue tasks\n",
        table(["ID", "Task", "Owner", "Due", "Days late", "Priority"],
              [(t.get("id"), t.get("title"), t.get("owner"), t["_due"], (as_of - t["_due"]).days, t.get("priority")) for t in tasks]),
        "## Open actions past due\n",
        table(["ID", "Action", "Owner", "Due"], [(a.get("id"), a.get("text"), a.get("owner"), a["_due"]) for a in acts]),
        f"## Milestones due within {days} days or overdue\n",
        table(["ID", "Milestone", "Due", "Status"], [(m.get("id"), m.get("title"), m["_due"], m.get("status")) for m in ms]),
        "## Open issues by severity\n",
        table(["ID", "Issue", "Severity", "Owner", "Status"],
              [(i.get("id"), i.get("title"), i.get("severity"), i.get("owner"), i.get("status")) for i in issues]),
        "## Open risks\n",
        table(["ID", "Risk", "Probability", "Impact", "Owner", "Status"],
              [(r.get("id"), r.get("title"), r.get("probability"), r.get("impact"), r.get("owner"), r.get("status")) for r in risks]),
    ]
    if bad:
        out += ["## Bad due dates\n", table(["Register", "ID", "Due"], bad)]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("--as-of", type=datetime.date.fromisoformat, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date to compare against (default: today)")
    ap.add_argument("--days", type=int, default=14, help="milestone window in days (default: 14)")
    args = ap.parse_args(argv)
    if args.days < 0:
        ap.error("--days cannot be negative")
    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")
    try:
        text = report(args.project, pc.load_config(args.project), args.as_of, args.days)
    except (pc.yaml.YAMLError, AttributeError, ValueError) as e:  # a register that is not `name:` plus a list of maps
        print(f"ERROR a register is not readable ({str(e).splitlines()[0]}); run render_views.py to see which", file=sys.stderr)
        return 2
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
