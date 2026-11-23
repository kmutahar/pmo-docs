#!/usr/bin/env python3
"""Move a project from schema_version 1 to 2: pad every id to project.id_width digits (default 3), then set schema_version to 2.

Usage:
    python3 0001_pad_ids.py [--yes] [--project ROOT]

The padding is `renumber.py --pad` (it prints a summary and asks yes or no; --yes skips the question).
A project that wants unpadded ids instead sets `project: {id_width: 0}` and `schema_version: 2` in pmo/config.yaml by hand.
The script can be repeated: schema_version is set last.
Exit codes: 0 migrated or already at version 2, 1 the registers failed validation afterwards, 2 usage, nothing confirmed, or a config the skill refuses.
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
import renumber  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("--yes", action="store_true", help="do not ask before padding")
    args = ap.parse_args(argv)
    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(args.project)
    text = pc.read(Path(args.project) / pc.CONFIG)
    mine = pc.load_yaml(text) or {}
    if mine.get("schema_version", 1) >= 2:
        print("schema_version is already 2, nothing to migrate")
        return 0
    # a schema 1 project without the key reads as 0; the migration pads to the default width
    cfg["project"]["id_width"] = (mine.get("project") or {}).get("id_width", 3)
    code = renumber.pad_main(args, cfg)
    if code != 0:
        return code
    new, n = re.subn(r"^schema_version:.*$", "schema_version: 2", text, count=1, flags=re.M)
    pc.safe_write(args.project, pc.CONFIG.as_posix(), new if n else "schema_version: 2\n" + text)
    print("schema_version is now 2")
    return 0


if __name__ == "__main__":
    sys.exit(pc.run(main))
