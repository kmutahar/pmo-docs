"""Shared helpers for the pmo-docs scripts: Python check, config merge, file lookup, front matter, registers."""
import sys

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

import copy
import datetime
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts" / "_vendor"))
import yaml  # noqa: E402  (vendored, loaded only with safe_load)

SCHEMA_VERSION = 1
CONFIG = Path("pmo/config.yaml")


def add_project_arg(parser):
    parser.add_argument("--project", default=".", help="project root (default: current folder)")


def read(path):
    return Path(path).read_text(encoding="utf-8")


def write(path, text):
    Path(path).write_text(text, encoding="utf-8")


def merge(base, over):
    """Maps merge, anything else replaces, None removes a map entry."""
    out = copy.deepcopy(base)
    for k, v in over.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(root="."):
    """Skill defaults merged with the project's pmo/config.yaml. Exits on a newer schema_version."""
    cfg = yaml.safe_load(read(SKILL / "assets" / "config.default.yaml"))
    f = Path(root) / CONFIG
    if f.exists():
        mine = yaml.safe_load(read(f)) or {}
        v = mine.get("schema_version", 1)
        if not isinstance(v, int) or v > SCHEMA_VERSION:
            print(f"{f}: schema_version {v!r} is newer than this skill knows ({SCHEMA_VERSION}). Update the skill.", file=sys.stderr)
            sys.exit(2)  # 2, not 1: callers read 1 as "findings"
        cfg = merge(cfg, mine)
    return cfg


def find_asset(root, cfg, kind, name):
    """(path, 'project' | 'skill') for a template: the project's file wins over the skill's default."""
    mine = Path(root) / cfg["paths"][kind] / name
    if mine.exists():
        return mine, "project"
    return SKILL / "assets" / kind / name, "skill"


def split_front_matter(text, strict=False):
    """(front matter dict or None when absent, body). Invalid YAML, or YAML that is not a map, gives {}, or raises yaml.YAMLError when strict."""
    m = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
        if not isinstance(fm, dict):
            raise yaml.YAMLError("front matter is not a map of keys")
        return fm, text[m.end():]
    except yaml.YAMLError:
        if strict:
            raise
        return {}, text[m.end():]


def doc_type(text):
    """A document's type is its front-matter `type` (a string), or None."""
    t = (split_front_matter(text)[0] or {}).get("type")
    return t if isinstance(t, str) else None


def load_register(root, cfg, name):
    """Entries of one register; a missing register or file is an empty list."""
    reg = cfg["registers"].get(name)
    f = Path(root) / cfg["paths"]["registers"] / reg["file"] if reg else None
    if not f or not f.exists():
        return []
    return (yaml.safe_load(read(f)) or {}).get(name) or []


def to_date(v):
    if not v:
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    return v if isinstance(v, datetime.date) else datetime.date.fromisoformat(str(v))


def cell(v):
    """A value as one Markdown table cell: lists joined, pipes escaped, newlines flattened."""
    if v is None or v == "":
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(cell(x) for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {cell(x)}" for k, x in v.items())
    return str(v).replace("|", "\\|").replace("\n", " ")
