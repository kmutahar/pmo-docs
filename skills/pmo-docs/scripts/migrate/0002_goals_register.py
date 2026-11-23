#!/usr/bin/env python3
"""Rename the `priorities` register to `goals` (a task's priority is its urgency level; a goal is an output with acceptance criteria).

Usage:
    python3 0002_goals_register.py [--project ROOT]

Part of the move from schema_version 1 to 2, with 0001_pad_ids.py (either order works). It
  - renames the register file (priorities.yaml -> goals.yaml), its top-level key and the entry field `goals` (a list of objective ids) to `objectives`,
  - rewrites the config: the `registers.priorities` key, and the `generated_from`, `refs` and `enums` entries that name it,
  - renames the ids P-n to GL-n (padded to project.id_width) in registers, documents and their translations, views, snapshots and names files, never inside code fences,
  - renames `priorities` in the front matter `source_hashes` of documents and moves the recorded hashes along, so a current document stays current,
  - deletes the old view and writes the new views.
It asks nothing. A project that set its own file name, view name or prefix for the register keeps them.
The script can be repeated: every step looks at what is left to do, and schema_version is not touched.
Exit codes: 0 migrated or nothing to do, 1 the registers failed validation afterwards, 2 usage, a config the skill refuses, or both priorities.yaml and goals.yaml exist.
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

OLD_PREFIX = "P"


def word(name):
    """A YAML key, list item or flow value spelled `name` by itself, not inside running text. Group 1 is what comes before it."""
    return re.compile(r"(^[ \t]*(?:-[ \t]+)?|[\[{,][ \t]*|:[ \t]+)" + re.escape(name) + r"(?=[ \t]*(?:$|[\]},:#]))", re.M)


def rename(text, old, new):
    """(new text, count) with the key or value `old` renamed to `new`."""
    return word(old).subn(lambda m: m[1] + new, text)


def rename_in_block(text, key, old, new):
    """(new text, count) with `old` renamed to `new` only below the mapping key `key`: its own line and the more indented lines after it."""
    out, indent, count = [], None, 0
    for line in text.split("\n"):
        m = re.match(r"([ \t]*)" + re.escape(key) + r":(?=[ \t]|$)", line)
        if m:
            indent = len(m[1])
            rest, n = rename(line[m.end():], old, new)
            line, count = line[:m.end()] + rest, count + n
        elif indent is not None and line.strip() and len(line) - len(line.lstrip()) > indent:
            line, n = rename(line, old, new)
            count += n
        elif line.strip():
            indent = None
        out.append(line)
    return "\n".join(out), count


def config_text(text, override):
    """(new config text, number of names changed). `override` is the project's registers.priorities map, or None."""
    n = 0
    if isinstance(override, dict):
        text, n = rename_in_block(text, "priorities", "goals", "objectives")
    text, m = rename(text, "priorities", "goals")
    return text, n + m


def register_text(text):
    """The old register file with its top-level key and its entry field renamed; unchanged when the key is already `goals`."""
    if not re.search(r"^priorities:", text, re.M):
        return text
    text = re.sub(r"(^[ \t]*(?:-[ \t]+)?|[{,][ \t]*)goals(?=[ \t]*:)", lambda m: m[1] + "objectives", text, flags=re.M)
    return re.sub(r"^priorities:", "goals:", text, count=1, flags=re.M)


def hashes_text(text):
    """A document with `priorities` renamed to `goals` in its front matter source_hashes."""
    m = pc.FRONT_MATTER.match(text)
    if not m or not m[1] or "source_hashes" not in m[1]:
        return text
    out, inside = [], False
    for line in m[1].split("\n"):
        if line.startswith("source_hashes:"):
            line, inside = "source_hashes:" + rename(line[len("source_hashes:"):], "priorities", "goals")[0], True
        elif inside and line[:1] in (" ", "\t"):
            line = rename(line, "priorities", "goals")[0]
        else:
            inside = False
        out.append(line)
    return text[:m.start(1)] + "\n".join(out) + text[m.end(1):]


def rename_ids(text, rx, prefix, width, fenced):
    """(new text, count) with every old id renamed to the new prefix and its number padded to width; lines inside code fences stay."""
    count, out, fence = 0, [], None

    def sub(m):
        nonlocal count
        count += 1
        return f"{prefix}-{m[1].zfill(width)}"

    for line in text.split("\n"):
        marker = re.match(r"\s*(```|~~~)", line) if fenced else None
        if marker and fence in (None, marker[1]):
            fence = None if fence else marker[1]
        elif not fence:
            line = rx.sub(sub, line)
        out.append(line)
    return "\n".join(out), count


def raw(root, rel):
    """The text of a file with its line endings kept."""
    return renumber.read_raw(Path(root) / rel)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    args = ap.parse_args(argv)
    root = Path(args.project)
    if not root.is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg_file = root / pc.CONFIG
    old_cfg = pc.read(cfg_file) if cfg_file.is_file() else ""
    mine = (pc.load_yaml(old_cfg) or {}) if old_cfg else {}
    regs = mine.get("registers") if isinstance(mine, dict) else None
    override = regs.get("priorities") if isinstance(regs, dict) else None
    new_cfg, n = config_text(old_cfg, override)
    if n:
        pc.safe_write(root, pc.CONFIG.as_posix(), new_cfg)
        print(f"config: renamed {n} names")
    override = override if isinstance(override, dict) else {}
    cfg = pc.load_config(root)
    goals = cfg["registers"].get("goals")
    if not isinstance(goals, dict):
        print("the goals register is turned off in the config: nothing to rename")
        return 0
    reg_dir, view_dir, docs = cfg["paths"]["registers"], cfg["paths"]["views"], cfg["paths"]["documents"]
    old_file = override.get("file") or "priorities.yaml"
    old_view = override.get("view") or "priorities.md"
    old_prefix = override.get("prefix", OLD_PREFIX)
    new_prefix = goals.get("prefix") or ""
    src, dst = root / reg_dir / old_file, root / reg_dir / goals["file"]

    moved = False
    if src != dst and src.is_file():
        if dst.exists():
            print(f"ERROR {reg_dir}/{old_file} and {reg_dir}/{goals['file']} both exist; merge them by hand, then run this again", file=sys.stderr)
            return 2
        src.rename(dst)
        moved = True
        print(f"registers: renamed {old_file} to {goals['file']}")
    old_view_path = root / view_dir / old_view
    if old_view != goals["view"] and old_view_path.is_file():
        old_view_path.unlink()
        print(f"views: removed {old_view}")

    files = renumber.pad_files(root, cfg)
    for rel in files:  # first, so that refresh_hashes finds the recorded hashes under their new name
        if rel.startswith(docs + "/") and rel.endswith(".md"):
            text = raw(root, rel)
            if hashes_text(text) != text:
                pc.safe_write(root, rel, hashes_text(text))
    pending = {}
    for rel in files:  # names files: register -> id -> field
        if not any(rel.startswith(cfg["paths"][k] + "/") for k in ("registers", "documents", "views", "snapshots")):
            text = raw(root, rel)
            if config_text(text, {})[0] != text:
                pending[rel] = config_text(text, {})[0]
    rel = f"{reg_dir}/{goals['file']}"
    if (root / rel).is_file():
        text = raw(root, rel)
        if register_text(text) != text:
            pending[rel] = register_text(text)
        rx = re.compile(r"(?<![A-Za-z0-9])" + re.escape(old_prefix) + r"-([0-9]+)(?![A-Za-z0-9])")
        if old_prefix != new_prefix and (moved or rx.search(text)):
            total = 0
            for f in files:
                cur = pending[f] if f in pending else raw(root, f)
                new, count = rename_ids(cur, rx, new_prefix, pc.id_width(cfg), f.endswith(".md"))
                if count:
                    pending[f], total = new, total + count
            print(f"ids: {old_prefix}-n renamed to {new_prefix}-n: {total} in {len(pending)} files")
    renumber.refresh_hashes(root, cfg, pending)
    for f, text in pending.items():
        pc.safe_write(root, f, text)
    return renumber.render_main(root)[0]


if __name__ == "__main__":
    sys.exit(pc.run(main))
