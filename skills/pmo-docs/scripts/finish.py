#!/usr/bin/env python3
"""Finish steps 5 to 7 on one draft: remove HTML comments and the `checks:` block, run the structure check, set `status: finished` and `last_updated`.

Usage:
    python3 finish.py [--as-of YYYY-MM-DD] [--project ROOT] FILE

Comments inside code fences stay. The file is written only when the structure check reports no errors; otherwise nothing changes and the errors are printed. Warnings are printed. Steps 1 to 4 (hashes, template version) and 8 to 9 (translations, snapshot) stay with the agent (`SKILL.md`, Finish).

Exit codes: 0 finished, 1 the structure check found errors or the document is not a draft, 2 usage, a config the skill refuses, or a file that is missing or outside the project.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
import structure_check  # noqa: E402

FENCE = re.compile(r"^\s*(```|~~~)")


def outside_fences(text, fn):
    """Apply fn to the parts of text that are not inside a code fence."""
    parts, fenced = [[False, ""]], False
    for line in text.splitlines(keepends=True):
        if FENCE.match(line):
            fenced = not fenced
            if fenced:  # an opening fence starts a kept part; the closing fence ends it
                parts.append([True, line])
                continue
            parts[-1][1] += line
            parts.append([False, ""])
            continue
        parts[-1][1] += line
    return "".join(s if kept else fn(s) for kept, s in parts)


def strip_comments(text):
    text = re.sub(r"^[ \t]*<!--.*?-->[ \t]*\n", "", text, flags=re.S | re.M)
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def drop_checks(text):
    """Remove the top-level `checks:` key (and its indented or `- ` lines) from the front matter."""
    m = pc.FRONT_MATTER.match(text)
    if not m or m.group(1) is None:
        return text
    kept, skipping = [], False
    for line in m.group(1).split("\n"):
        if re.match(r"checks:", line):
            skipping = True
            continue
        if skipping and (line.startswith((" ", "\t", "- ")) or not line.strip()):
            continue
        skipping = False
        kept.append(line)
    return "---\n" + "\n".join(kept) + "\n---\n" + text[m.end():]


def set_status(text, day):
    m = pc.FRONT_MATTER.match(text)
    head = m.group(1)
    head = re.sub(r"^status:.*$", "status: finished", head, flags=re.M)
    head = re.sub(r'^last_updated:[ \t]*(")?.*$', lambda g: f'last_updated: "{day}"' if g.group(1) else f"last_updated: {day}", head, flags=re.M)
    return "---\n" + head + "\n---\n" + text[m.end():]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("--as-of", type=pc.as_of, default=datetime.date.today(), metavar="YYYY-MM-DD", help="date for last_updated (default: today)")
    ap.add_argument("file", help="the draft to finish")
    a = ap.parse_args(argv)
    root = Path(a.project).resolve()
    if not root.is_dir():
        ap.error(f"project folder not found: {a.project}")
    f = Path(a.file).resolve()
    if root not in f.parents:
        print(f"{a.file} is outside the project", file=sys.stderr)
        return 2
    if not f.is_file():
        print(f"{a.file} is not a file", file=sys.stderr)
        return 2
    cfg = pc.load_config(root)
    text = pc.read(f)
    fm, _ = pc.split_front_matter(text)
    if not fm or fm.get("status") != "draft":
        print(f"{f.relative_to(root)}: not a draft (status: {(fm or {}).get('status')}); nothing changed")
        return 1
    new = drop_checks(outside_fences(text, strip_comments))
    errors, warns = structure_check.check(root, cfg, new)
    rel = f.relative_to(root)
    for w in warns:
        print(f"warn  {rel}: {w}")
    if errors:
        for e in errors:
            print(f"ERROR {rel}: {e}")
        print("nothing changed: fix the errors, then run finish.py again")
        return 1
    pc.write(f, set_status(new, a.as_of.isoformat()))
    print(f"finished: {rel} (last_updated {a.as_of.isoformat()})")
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
