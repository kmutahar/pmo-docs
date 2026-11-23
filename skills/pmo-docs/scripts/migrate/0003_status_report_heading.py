#!/usr/bin/env python3
"""Rename the status report heading in a project's template overrides: `## Risks and issues` becomes `## Risks and issues: changes since last report`.

Usage:
    python3 0003_status_report_heading.py [--project ROOT]

Looks at the status report templates in the project's templates folder (status-report.md and copies of it, such as a file whose front matter says `type: status-report`; translations such as status-report.ar.md are left alone).
A file changes only when it has the old heading and not the new one. Prints one line per file changed. It asks nothing and can be repeated.
Part of the move from schema_version 1 to 2 (run it after 0001 and 0002; it does not touch schema_version).
Exit codes: 0 done or nothing to do, 2 usage or a config the skill refuses.
"""
import argparse
import re
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pmo_common as pc  # noqa: E402
from renumber import read_raw  # noqa: E402

OLD = re.compile(r"^## Risks and issues([ \t]*\r?)$", re.M)
NEW = "## Risks and issues: changes since last report"
TRANSLATION = re.compile(r"\.[a-z]{2,3}(-[A-Za-z0-9]+)?\.md$")
TYPE = re.compile(r"^type:[ \t]*[\"']?status-report[\"']?[ \t]*$", re.M)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    args = ap.parse_args(argv)
    root = Path(args.project)
    if not root.is_dir():
        ap.error(f"project folder not found: {args.project}")
    folder = root / pc.load_config(root)["paths"]["templates"]
    for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        if TRANSLATION.search(f.name):
            continue
        text = read_raw(f)
        front = pc.FRONT_MATTER.match(text)
        if not (f.name.startswith("status-report") or front and front[1] and TYPE.search(front[1])):
            continue
        if not OLD.search(text) or re.search("^" + re.escape(NEW) + r"[ \t]*\r?$", text, re.M):
            continue
        rel = f.relative_to(root).as_posix()
        pc.safe_write(root, rel, OLD.sub(lambda m: NEW + m[1], text, count=1))
        print(f"{rel}: renamed `## Risks and issues` to `{NEW}`")
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
