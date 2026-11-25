#!/usr/bin/env python3
"""Update fields on one existing register entry, validating before writing.

Usage:
    python3 register.py [--project ROOT] set <register> <key> FIELD=VALUE [FIELD=VALUE ...]

<key> is the entry id (e.g. T-001 or short form T-1), `slug` for `roster`, or
`<period>/<person>` (e.g. 2026-03/alice) for `capacity`.

Exit codes:
    0 updated (or unchanged)
    1 validation error or unreadable register
    2 usage, missing register or entry, or config error
"""
import argparse
import copy
import datetime
import json
import re
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402

NUMERIC_FIELDS = {
    ("teams", "order"),
    ("capacity", "working_days"),
    ("capacity", "leave_days"),
    ("budget", "low"),
    ("budget", "medium"),
    ("budget", "high"),
}
BOOLEAN_FIELDS = {("tests", "regression")}
PLAIN_FORBIDDEN = set(',:#{}[]"\'\\&*!|>%@`?\n\r\t\u2028\u2029\x85')


def _json_quote(text: str) -> str:
    return (
        json.dumps(text, ensure_ascii=False)
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
        .replace("\x85", "\\x85")
    )


def _format_key(key) -> str:
    k = str(key)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k):
        return k
    return _json_quote(k)


def _plain_ok(text: str, is_date: bool) -> bool:
    if not text or text != text.strip() or text.startswith("-"):
        return False
    if any(ch in PLAIN_FORBIDDEN for ch in text):
        return False
    try:
        parsed = pc.load_yaml(f"v: {text}")
    except (pc.yaml.YAMLError, ValueError):
        return False
    if not isinstance(parsed, dict) or "v" not in parsed:
        return False
    val = parsed["v"]
    if is_date:
        return bool(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text)) and str(val) == text
    return isinstance(val, str) and val == text


def format_val(val, is_date: bool = False) -> str:
    """Serialize one YAML flow value on a single line."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
        return val.isoformat()
    if isinstance(val, list):
        return "[" + ", ".join(format_val(x, is_date=False) for x in val) + "]"
    if isinstance(val, dict):
        return "{" + ", ".join(f"{_format_key(k)}: {format_val(v, is_date=False)}" for k, v in val.items()) + "}"
    s = str(val)
    if s == "":
        return '""'
    if _plain_ok(s, is_date):
        return s
    return _json_quote(s)


def format_entry(entry: dict, reg: dict, old_line: str) -> str:
    """Format an entry dict as a single-line YAML flow mapping preserving indentation."""
    m = re.match(r"^(\s*-\s*)", old_line)
    prefix = m.group(1) if m else "  - "
    dates = set(reg.get("dates") or [])
    items = [f"{_format_key(k)}: {format_val(v, is_date=(k in dates))}" for k, v in entry.items()]
    return f"{prefix}{{{', '.join(items)}}}"


def parse_value(reg_name: str, reg: dict, field: str, raw: str):
    """Parse a FIELD=VALUE string safely without accidental YAML 1.1 type coercion."""
    if raw in ("null", "~"):
        return None
    if raw == "":
        return ""
    dates = set(reg.get("dates") or [])
    months = set(reg.get("months") or [])
    if field in dates or field in months or (reg_name == "tasks" and field == "wbs"):
        return raw
    if (reg_name, field) in NUMERIC_FIELDS:
        if re.fullmatch(r"-?[0-9]+", raw):
            return int(raw)
        if re.fullmatch(r"-?[0-9]+\.[0-9]+", raw):
            return float(raw)
        return raw
    if (reg_name, field) in BOOLEAN_FIELDS:
        if raw == "true":
            return True
        if raw == "false":
            return False
        return raw
    if (raw.startswith("[") and raw.endswith("]")) or (raw.startswith("{") and raw.endswith("}")):
        parsed = pc.load_yaml(raw)
        if isinstance(parsed, (list, dict)):
            return parsed
    return raw


def _same_value(old_val, new_val, is_date: bool) -> bool:
    if is_date and isinstance(old_val, datetime.date) and not isinstance(old_val, datetime.datetime):
        return old_val.isoformat() == new_val
    return type(old_val) is type(new_val) and old_val == new_val


def _display_val(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, datetime.date) and not isinstance(v, datetime.datetime):
        return v.isoformat()
    if v == "":
        return '""'
    return str(v)


def _find_matches(reg_name: str, reg: dict, cfg: dict, raw_entries: list[dict], key: str) -> tuple[list[int], tuple[str, ...], str | None]:
    """Return (matching indices, immutable key fields, error message or None)."""
    fields = reg.get("fields") or []
    if "id" in fields:
        matches = [i for i, e in enumerate(raw_entries) if str(e.get("id")) == key]
        if not matches and reg.get("prefix"):
            if re.fullmatch(re.escape(reg["prefix"]) + r"-[0-9]+", key):
                padded = pc.unpadded(key, pc.id_width(cfg))
                if padded:
                    matches = [i for i, e in enumerate(raw_entries) if str(e.get("id")) == padded]
        return matches, ("id",), None
    if "slug" in fields:
        matches = [i for i, e in enumerate(raw_entries) if str(e.get("slug")) == key]
        return matches, ("slug",), None
    if "period" in fields and "person" in fields:
        if "/" not in key:
            return [], ("period", "person"), f"{reg_name} key must be <period>/<person> (for example 2026-03/alice)"
        period, person = key.split("/", 1)
        if not period or not person:
            return [], ("period", "person"), f"{reg_name} key must be <period>/<person> (for example 2026-03/alice)"
        matches = [i for i, e in enumerate(raw_entries) if str(e.get("period")) == period and str(e.get("person")) == person]
        return matches, ("period", "person"), None
    return [], (), f"register {reg_name!r} has no id, slug, or period/person key"


def _cmd_set(args) -> int:
    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"ERROR project folder not found: {args.project}", file=sys.stderr)
        return 2

    cfg = pc.load_config(root)
    if bad := render_views.config_errors(cfg, root=root):
        print("\n".join("ERROR " + e for e in bad), file=sys.stderr)
        return 2

    if args.register not in cfg["registers"]:
        print(f"ERROR unknown register {args.register!r}; known: {', '.join(sorted(cfg['registers']))}", file=sys.stderr)
        return 2

    reg = cfg["registers"][args.register]
    rel_file = f"{cfg['paths']['registers']}/{reg['file']}"
    pc.check_inside(root, rel_file)
    reg_path = root / rel_file
    if not reg_path.is_file():
        print(f"ERROR register file not found: {rel_file}", file=sys.stderr)
        return 2

    data, read_errors = render_views.read_registers(root, cfg)
    if read_errors:
        for err in read_errors:
            print("ERROR", err, file=sys.stderr)
        return 1

    raw_text = pc.read(reg_path)
    elines = render_views.entry_lines(raw_text)
    parsed_raw = pc.load_yaml(raw_text)
    raw_entries = (parsed_raw or {}).get(args.register) or []
    if len(raw_entries) != len(elines):
        print(f"ERROR {rel_file}: every entry must be on one line", file=sys.stderr)
        return 1

    matches, immutable_keys, key_err = _find_matches(args.register, reg, cfg, raw_entries, args.key)
    if key_err:
        print(f"ERROR {key_err}", file=sys.stderr)
        return 2
    if not matches:
        print(f"ERROR {args.register}: entry {args.key!r} not found", file=sys.stderr)
        return 2
    if len(matches) > 1:
        print(f"ERROR {args.register}: multiple entries match {args.key!r}; run renumber.py first", file=sys.stderr)
        return 1

    idx = matches[0]
    lineno = elines[idx]
    orig_entry = raw_entries[idx]
    display_key = str(orig_entry.get("id")) if "id" in immutable_keys else args.key

    updates = {}
    for item in args.assignments:
        if "=" not in item:
            print(f"ERROR invalid assignment {item!r}; use FIELD=VALUE", file=sys.stderr)
            return 2
        field, raw_val = item.split("=", 1)
        if not field:
            print(f"ERROR invalid assignment {item!r}; field name cannot be empty", file=sys.stderr)
            return 2
        if field in updates:
            print(f"ERROR duplicate field {field!r} in one command", file=sys.stderr)
            return 2
        if field in immutable_keys:
            hint = "; use renumber.py for duplicates" if field == "id" else ""
            print(f"ERROR cannot change {field} with register.py{hint}", file=sys.stderr)
            return 2
        try:
            updates[field] = parse_value(args.register, reg, field, raw_val)
        except (pc.yaml.YAMLError, ValueError) as e:
            first_line = str(e).splitlines()[0] if str(e).splitlines() else str(e)
            print(f"ERROR invalid value for {field}: {first_line}", file=sys.stderr)
            return 2

    fields_order = list(reg.get("fields") or [])
    new_entry = {}
    for k, v in orig_entry.items():
        new_entry[k] = updates[k] if k in updates else v
    for k in fields_order:
        if k in updates and k not in new_entry:
            new_entry[k] = updates[k]
    for k, v in updates.items():
        if k not in new_entry:
            new_entry[k] = v

    dates = set(reg.get("dates") or [])
    changed = []
    for k, new_v in updates.items():
        if k not in orig_entry or not _same_value(orig_entry[k], new_v, k in dates):
            old_v = orig_entry.get(k)
            changed.append((k, _display_val(old_v), _display_val(new_v)))

    lines = raw_text.split("\n")
    old_line = lines[lineno - 1]
    new_line = format_entry(new_entry, reg, old_line)
    lines[lineno - 1] = new_line
    new_text = "\n".join(lines)

    if not render_views.one_line_entries(new_text):
        print(f"ERROR {rel_file}: serialized entry is not a single line", file=sys.stderr)
        return 1
    try:
        reparsed = pc.load_yaml(new_text)
    except (pc.yaml.YAMLError, ValueError) as e:
        first_line = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        print(f"ERROR {rel_file}: serialized YAML invalid ({first_line})", file=sys.stderr)
        return 1

    new_entries = (reparsed or {}).get(args.register) or []
    pc.apply_defaults(reg, new_entries)
    val_data = copy.deepcopy(data)
    val_data[args.register] = new_entries

    val_errors = render_views.validate(val_data, cfg, root=root)
    if val_errors:
        for err in val_errors:
            print("ERROR", err, file=sys.stderr)
        return 1

    if not changed:
        print(f"unchanged: {args.register} {display_key}")
        return 0

    pc.safe_write(root, rel_file, new_text)
    summary = ", ".join(f"{k}: {old} -> {new}" for k, old, new in changed)
    print(f"updated: {args.register} {display_key} ({summary})")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("set", help="update fields on one existing register entry")
    sp.add_argument("--project", default=argparse.SUPPRESS, help="project root (default: current folder)")
    sp.add_argument("register", help="register name (e.g. tasks, risks, roster, capacity)")
    sp.add_argument("key", help="entry id (e.g. T-001), roster slug, or <period>/<person> for capacity")
    sp.add_argument("assignments", nargs="+", metavar="FIELD=VALUE", help="field updates as FIELD=VALUE")
    args = ap.parse_args(argv)
    return _cmd_set(args)


if __name__ == "__main__":
    sys.exit(pc.run(main))
