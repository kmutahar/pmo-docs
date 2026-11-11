#!/usr/bin/env python3
"""Set up the project's pmo/ folder deterministically."""
import argparse
import contextlib
import io
import shutil
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Set up the project's pmo/ folder deterministically.")
    pc.add_project_arg(ap)
    ap.add_argument("--name", default=None, help="project name")
    ap.add_argument("--manager", default=None, help="project manager name")
    ap.add_argument("--priority-order", default=None,
                    help="comma-separated priority order (most urgent first)")
    ap.add_argument("--week-start", choices=pc.WEEKDAYS, default="monday",
                    help="first day of the week (default monday)")
    args = ap.parse_args(argv)

    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")

    priority_order = None
    if args.priority_order is not None:
        parts = [p.strip() for p in args.priority_order.split(",")]
        if any(not p for p in parts):
            ap.error(f"invalid --priority-order: {args.priority_order!r}")
        priority_order = parts

    cfg_file = Path(args.project) / pc.CONFIG
    if cfg_file.exists():
        print("already set up: pmo/config.yaml exists, nothing written")
        try:
            mine = pc.yaml.safe_load(pc.read(cfg_file)) or {}
        except Exception:
            mine = {}
        v = mine.get("schema_version", 1) if isinstance(mine, dict) else 1
        if not isinstance(v, int):
            v = 1
        if v == pc.SCHEMA_VERSION:
            print("schema_version is current")
        elif v < pc.SCHEMA_VERSION:
            print("a migration is due (none exist yet)")
        else:
            print("the skill is out of date, update it")
            return 2
        return 0

    cfg = pc.load_config(args.project)
    paths = cfg["paths"]
    reg_dir = Path(args.project) / paths["registers"]
    house_rules_file = Path(args.project) / paths["house_rules"]
    docs_dir = Path(args.project) / paths["documents"]

    actions = []

    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    mine = {
        "schema_version": pc.SCHEMA_VERSION,
        "project": {
            "name": args.name,
            "manager": args.manager,
        },
    }
    if args.week_start != "monday":
        mine["project"]["week_start"] = args.week_start
    if priority_order is not None:
        mine["vocab"] = {"priority_order": priority_order}

    pc.write(cfg_file, pc.yaml.safe_dump(mine, sort_keys=False))
    actions.append(f"created: {pc.CONFIG.as_posix()}")

    starter_dir = pc.SKILL / "assets" / "starter" / "registers"
    reg_dir.mkdir(parents=True, exist_ok=True)
    for name, r in cfg.get("registers", {}).items():
        rf = r["file"]
        dest = reg_dir / rf
        rel_dest = f"{paths['registers']}/{rf}"
        if dest.exists():
            actions.append(f"kept: {rel_dest}")
        else:
            src = starter_dir / rf
            if src.exists():
                shutil.copyfile(src, dest)
                actions.append(f"created: {rel_dest}")

    rel_hr = paths["house_rules"]
    if house_rules_file.exists():
        actions.append(f"kept: {rel_hr}")
    else:
        house_rules_file.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "# House rules\n\n"
            "This project's own rules go here.\n\n"
            "Rules defined here take precedence over the skill's rules,\n"
            "except for the safety rules in the skill's SKILL.md.\n"
        )
        pc.write(house_rules_file, content)
        actions.append(f"created: {rel_hr}")

    docs_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = docs_dir / ".gitkeep"
    rel_gitkeep = f"{paths['documents']}/.gitkeep"
    if gitkeep.exists():
        actions.append(f"kept: {rel_gitkeep}")
    else:
        pc.write(gitkeep, "")
        actions.append(f"created: {rel_gitkeep}")

    rv_script = Path(__file__).resolve().parent / "render_views.py"
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = render_views.main(["--project", str(args.project)])
    except SystemExit as e:
        code = e.code or 0
        if isinstance(code, str):
            out.write(code + "\n")
            code = 1
    if code != 0:
        sys.stdout.write(out.getvalue())
        return 1

    for act in actions:
        print(act)
    print()
    print("next: add your first tasks, or draft the project charter")
    print(f"optional hook line: python3 {rv_script.resolve()} --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
