"""Shared helpers for the pmo-docs scripts: Python check, config merge, file lookup, front matter, registers."""
import sys

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.dont_write_bytecode = True

import copy
import datetime
import hashlib
import os
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts" / "_vendor"))
import yaml  # noqa: E402  (vendored, loaded only with safe_load and the SafeLoader subclass below)
import yaml.composer  # noqa: E402
import yaml.constructor  # noqa: E402

SCHEMA_VERSION = 1
CONFIG = Path("pmo/config.yaml")
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
LANG_CODE = re.compile(r"[a-z]{2,3}(-[A-Za-z0-9]{2,8})?")
BACKSLASH = chr(92)
FRONT_MATTER = re.compile(r"\A---[ \t]*\n(?:(.*?)\n)?---[ \t]*(?:\n|\Z)", re.S)


def add_project_arg(parser):
    parser.add_argument("--project", default=".", help="project root (default: current folder)")


def read(path):
    """Read a UTF-8 text file. A BOM is dropped when a document is read and written back."""
    return Path(path).read_text(encoding="utf-8-sig")


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


def outside(root, *parts):
    """resolve() follows symlinks and '..', so this catches a committed symlink or '..' out of the project, or into .git."""
    root_r = Path(root).resolve()
    try:
        rel = (root_r / Path(*parts)).resolve().relative_to(root_r)
    except ValueError:
        return True
    return ".git" in rel.parts


def check_inside(root, rel):
    if outside(root, rel):
        print(f"{rel}: must stay inside the project", file=sys.stderr)
        sys.exit(2)


def safe_write(root, rel, text):
    check_inside(root, rel)
    write(Path(root) / rel, text)


def config_type_errors(cfg) -> list[str]:
    """Type checks on cfg: project, registers, vocab, doc_types. Returns list of messages without prefix."""
    errors = []
    if "project" in cfg and not isinstance(cfg["project"], dict):
        errors.append("project must be a map")

    for name, r in cfg.get("registers", {}).items():
        if not isinstance(r, dict):
            continue
        if "prefix" in r and not isinstance(r["prefix"], str):
            errors.append(f"registers.{name}.prefix must be text")
        for k in ("fields", "dates", "months", "closed", "done", "blocked", "active", "accepted"):
            if k in r:
                val = r[k]
                if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                    errors.append(f"registers.{name}.{k} must be a list of text")
        if "enums" in r:
            val = r["enums"]
            if not isinstance(val, dict) or not all(isinstance(v, str) for v in val.values()):
                errors.append(f"registers.{name}.enums must be a map of text")

    for k, v in cfg.get("vocab", {}).items():
        if not isinstance(v, list):
            errors.append(f"vocab.{k} must be a list")

    for dtype, dt in cfg.get("doc_types", {}).items():
        if not isinstance(dt, dict):
            errors.append(f"doc_types.{dtype} must be a map")
            continue
        for k in ("name", "title", "template"):
            if k in dt:
                val = dt[k]
                if not isinstance(val, str):
                    errors.append(f"doc_types.{dtype}.{k} must be text")
                elif k in ("name", "title"):
                    if "/" in val or BACKSLASH in val or val == "..":
                        errors.append(f"doc_types.{dtype}.{k} must not contain a slash or a backslash")
        if "stale_days" in dt:
            val = dt["stale_days"]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                errors.append(f"doc_types.{dtype}.stale_days must be a number")

    return errors


class _StrictLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        event = self.peek_event()
        if getattr(event, "anchor", None) is not None:
            raise yaml.composer.ComposerError(None, None, "anchors and aliases are not allowed", event.start_mark)
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            seen = set()
            for key_node, _ in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":
                    raise yaml.constructor.ConstructorError(None, None, "merge keys (<<) are not allowed", key_node.start_mark)
                key = self.construct_object(key_node, deep=True)
                try:
                    hash(key)
                except TypeError:
                    continue
                if key in seen:
                    raise yaml.constructor.ConstructorError(None, None, f"found a repeated key {key!r}", key_node.start_mark)
                seen.add(key)
        return super().construct_mapping(node, deep=deep)


def load_yaml(text):
    """Parse YAML with _StrictLoader: repeated keys, anchors, aliases and merge keys (<<) are refused."""
    loader = _StrictLoader(text)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def load_config(root=".", must_exist=True):
    """Skill defaults merged with the project's pmo/config.yaml. Exits 2 on a newer schema_version, missing/invalid config, or paths that leave the project."""
    cfg = yaml.safe_load(read(SKILL / "assets" / "config.default.yaml"))
    required_paths = list(cfg["paths"])
    f = Path(root) / CONFIG
    if not f.exists():
        if must_exist:
            print(f"{root}: no pmo/config.yaml here; run setup.py first, or pass --project", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            text = read(f)
            mine = load_yaml(text) or {}
        except UnicodeDecodeError:
            print(f"{f}: not valid UTF-8 text", file=sys.stderr)
            sys.exit(2)
        except (yaml.YAMLError, ValueError) as e:
            first_line = str(e).splitlines()[0] if str(e).splitlines() else str(e)
            print(f"{f}: not valid YAML: {first_line}", file=sys.stderr)
            sys.exit(2)
        except OSError as e:
            first_line = str(e).splitlines()[0] if str(e).splitlines() else str(e)
            print(f"{f}: cannot be read ({first_line})", file=sys.stderr)
            sys.exit(2)
        if not isinstance(mine, dict):
            print(f"{f}: must be a YAML map of keys, got {type(mine).__name__}", file=sys.stderr)
            sys.exit(2)
        v = mine.get("schema_version", 1)
        if type(v) is not int or v < 1:
            print(f"{f}: schema_version must be a whole number of 1 or more (got {v!r})", file=sys.stderr)
            sys.exit(2)
        elif v > SCHEMA_VERSION:
            print(f"{f}: schema_version {v!r} is newer than this skill knows ({SCHEMA_VERSION}). Update the skill.", file=sys.stderr)
            sys.exit(2)  # 2, not 1: callers read 1 as "findings"
        cfg = merge(cfg, mine)
    for key in ("paths", "registers", "doc_types", "vocab"):  # `paths: null` removes the key, a list or text is not a map
        if not isinstance(cfg.get(key), dict):
            print(f"{f}: `{key}` must be a map", file=sys.stderr)
            sys.exit(2)

    for key in required_paths:
        if key not in cfg["paths"]:
            print(f"{f}: paths.{key} is missing", file=sys.stderr)
            sys.exit(2)

    errs = config_type_errors(cfg)
    if errs:
        for err in errs:
            print(f"ERROR config: {err}", file=sys.stderr)
        sys.exit(2)

    def is_outside(*parts):
        return outside(root, *parts)

    bad = [f"paths.{k}: {p!r}" for k, p in cfg["paths"].items() if not isinstance(p, str) or not p or is_outside(p)]
    for n, r in cfg["registers"].items():
        if not isinstance(r, dict):
            continue  # render_views.config_errors reports it
        for k, kind in (("file", "registers"), ("view", "views")):
            x, base = r.get(k), cfg["paths"].get(kind)
            if k in r and (not isinstance(x, str) or Path(x).name in ("", "..") or Path(x).name != x
                           or (isinstance(base, str) and base and is_outside(base, x))):
                bad.append(f"registers.{n}.{k}: {x!r}")
    if bad:
        print(f"{f}: these must stay inside the project (no absolute paths, '..', symlinks out or '.git'; register file and view bare file names): {'; '.join(bad)}", file=sys.stderr)
        sys.exit(2)
    return cfg


def find_asset(root, cfg, kind, name):
    """(path, 'project' | 'skill') for a template or playbook: the project's file wins over the skill's default."""
    p = Path(name)
    if "\\" in name or p.is_absolute() or ".." in p.parts:
        raise ValueError(f"invalid asset name {name!r}")
    if p.parts and p.parts[0] == "stacks":
        if len(p.parts) != 2 or not p.parts[1].endswith(".md"):
            raise ValueError(f"invalid stack asset name {name!r}")
        stack = p.parts[1][:-3]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", stack):
            raise ValueError(f"invalid stack asset name {name!r}")
    if outside(root, cfg["paths"][kind], name):
        raise ValueError(f"asset leaves project: {name!r}")
    mine = Path(root) / cfg["paths"][kind] / name
    if mine.exists():
        return mine, "project"
    if kind == "playbooks":
        return SKILL / "references" / name, "skill"
    return SKILL / "assets" / kind / name, "skill"


def split_front_matter(text, strict=False):
    """(front matter dict or None when absent, body). Invalid YAML, or YAML that is not a map, gives {}, or raises yaml.YAMLError when strict."""
    # shortcut: pc.read() uses Path.read_text(), which normalises \r\n to \n across all callers
    m = FRONT_MATTER.match(text)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1) or "") or {}
        if not isinstance(fm, dict):
            raise yaml.YAMLError("front matter is not a map of keys")
        return fm, text[m.end():]
    except (yaml.YAMLError, ValueError) as e:
        if strict:
            if isinstance(e, yaml.YAMLError):
                raise e
            raise yaml.YAMLError(str(e))
        return {}, text[m.end():]


def languages(cfg) -> dict:
    """{'draft': 'en', 'translations': ['xx'], 'info': {code: block}} from cfg['languages']. A missing or empty block gives English only; translations holds valid, non-repeated language codes different from draft; 'info' holds the draft code and every translation code (an absent block is {})."""
    block = cfg.get("languages") if isinstance(cfg, dict) else None
    if not isinstance(block, dict):
        block = {}
    draft = block.get("draft")
    if not isinstance(draft, str) or not draft:
        draft = "en"
    raw_trans = block.get("translations")
    translations = []
    seen = set()
    if isinstance(raw_trans, list):
        for t in raw_trans:
            if isinstance(t, str) and LANG_CODE.fullmatch(t) and t != draft and t not in seen:
                translations.append(t)
                seen.add(t)
    codes = [draft] + translations
    info = {}
    for c in codes:
        val = block.get(c)
        info[c] = copy.deepcopy(val) if isinstance(val, dict) else {}
    return {"draft": draft, "translations": translations, "info": info}


def _doc_type(cfg, doc_type):
    """The doc_types.<type> map, or None when doc_types or the type is not a map."""
    dt = cfg.get("doc_types")
    info = dt.get(doc_type) if isinstance(dt, dict) else None
    return info if isinstance(info, dict) else None


def type_translations(cfg, doc_type) -> list[str]:
    """doc_types.<type>.translations if the key is present (a list, [] = none), else languages.translations."""
    dt_info = _doc_type(cfg, doc_type)
    if dt_info and "translations" in dt_info:
        val = dt_info.get("translations")
        return list(val) if isinstance(val, list) else []
    return languages(cfg)["translations"]


def register_prefixes(cfg) -> list[str]:
    """Non-empty register prefixes from cfg (or defaults), longest first then alphabetical."""
    regs = cfg.get("registers") if isinstance(cfg, dict) else None
    if not isinstance(regs, dict):
        regs = {}
    prefixes = [r["prefix"] for r in regs.values() if isinstance(r, dict) and isinstance(r.get("prefix"), str) and r["prefix"]]
    if not prefixes:
        prefixes = ["T", "P", "M", "R", "I", "A", "D", "DEC", "CR", "ACT", "MTG", "TM"]
    return sorted(set(prefixes), key=lambda x: (-len(x), x))


def translate_flag(cfg, doc_type) -> str:
    """doc_types.<type>.translate, default 'in-period'."""
    dt_info = _doc_type(cfg, doc_type)
    if dt_info:
        val = dt_info.get("translate")
        if val is not None:
            return str(val)
    return "in-period"


def translation_rel(doc_rel: str, lang: str) -> str:
    """'a/b.md' -> 'a/b.xx.md'. ValueError when doc_rel does not end in '.md'."""
    if not doc_rel.endswith(".md"):
        raise ValueError(f"doc_rel must end in '.md': {doc_rel!r}")
    return doc_rel[:-3] + f".{lang}.md"


def body_hash(text: str) -> str:
    """8 hex characters of the SHA-256 of the document body: front matter removed (split_front_matter), HTML comments removed, every line right-stripped, blank lines dropped, lines joined with one newline, UTF-8."""
    _, body = split_front_matter(text)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    lines = [ln.rstrip() for ln in body.splitlines()]
    non_blank = [ln for ln in lines if ln]
    joined = "\n".join(non_blank)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:8]


def glossary_paths(cfg, lang: str) -> tuple[str | None, str | None]:
    """(approved, proposed) paths as written in the config, or (None, None) without a glossary. proposed = same folder, '<stem>.proposed.md'."""
    langs = cfg.get("languages") if isinstance(cfg, dict) else None
    if not isinstance(langs, dict):
        return None, None
    block = langs.get(lang)
    if not isinstance(block, dict):
        return None, None
    g = block.get("glossary")
    if not isinstance(g, str) or not g.strip():
        return None, None
    if g.endswith(".md"):
        proposed = g[:-3] + ".proposed.md"
    else:
        p = Path(g)
        proposed = f"{p.parent.as_posix()}/{p.stem}.proposed{p.suffix}" if str(p.parent) != "." else f"{p.stem}.proposed{p.suffix}"
    return g, proposed


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
    data = load_yaml(read(f))
    if data is None:
        return []
    if not isinstance(data, dict) or name not in data:
        msg = f"{f.name}: top key must be {name}:"
        raise ValueError(msg)
    entries = data.get(name)
    return entries or []


def to_date(v):
    if not v:
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    s = str(v)
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", s):
        raise ValueError(f"not a YYYY-MM-DD date: {v!r}")
    return datetime.date.fromisoformat(s)


def cell(v):
    """A value as one Markdown table cell: lists joined, pipes escaped (and the backslashes right before one), carriage returns and newlines flattened."""
    if v is None or v == "":
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(cell(x) for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {cell(x)}" for k, x in v.items())
    s = str(v).replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"(\\*)\|", lambda m: m.group(1) * 2 + "\\|", s)


def inline(v):
    """A value as one line of text: any run of white space becomes one space."""
    return " ".join(str(v).split())


def week_start(cfg) -> int:
    """0 for Monday ... 6 for Sunday, from project.week_start (default monday). ValueError on an unknown name."""
    ws = cfg.get("project", {}).get("week_start", "monday") if isinstance(cfg.get("project"), dict) else "monday"
    if ws is None:
        ws = "monday"
    if not isinstance(ws, str) or ws.lower() not in WEEKDAYS:
        raise ValueError(f"unknown week_start: {ws!r}")
    return WEEKDAYS.index(ws.lower())


def week_of(day: datetime.date, start: int) -> str:
    """'YYYY-Www' of the week holding `day`: the ISO week of that week's fourth day."""
    if not 0 <= start <= 6:
        raise ValueError(f"start weekday must be 0..6, got {start}")
    offset = (day.weekday() - start) % 7
    first_day = day - datetime.timedelta(days=offset)
    fourth_day = first_day + datetime.timedelta(days=3)
    iso_year, iso_week, _ = fourth_day.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def period_range(period: str, start: int) -> tuple[datetime.date, datetime.date]:
    """First and last day (inclusive) of 'YYYY-MM' or 'YYYY-Www'. ValueError for anything else, including a week 53 in a 52-week year."""
    if not 0 <= start <= 6:
        raise ValueError(f"start weekday must be 0..6, got {start}")
    if m := re.fullmatch(r"([0-9]{4})-(0[1-9]|1[0-2])", period):
        year, month = int(m.group(1)), int(m.group(2))
        first = datetime.date(year, month, 1)
        if month == 12:
            last = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        return first, last
    if m := re.fullmatch(r"([0-9]{4})-W(0[1-9]|[1-4][0-9]|5[0-3])", period):
        year, week = int(m.group(1)), int(m.group(2))
        iso_weekday = ((start + 3) % 7) + 1
        fourth = datetime.date.fromisocalendar(year, week, iso_weekday)
        first = fourth - datetime.timedelta(days=3)
        last = first + datetime.timedelta(days=6)
        return first, last
    raise ValueError(f"invalid period {period!r}; use YYYY-MM or YYYY-Www")


def resolve_period(period: str | None, week: bool, as_of: datetime.date, start: int) -> str:
    """The period a command means: the given one (validated, same regex as where.py today), else the week of as_of (week=True), else as_of's month."""
    if period:
        if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2]|W(0[1-9]|[1-4][0-9]|5[0-3]))", period):
            raise ValueError(f"invalid period {period!r}; use YYYY-MM or YYYY-Www")
        return period
    if week:
        return week_of(as_of, start)
    return as_of.strftime("%Y-%m")


def doc_rel_path(cfg, doc_type: str, period: str, as_of: datetime.date, title: str | None = None) -> str:
    """'<paths.documents>/<name>' with {title}, {period} and {date} filled, as where.py does today."""
    info = cfg.get("doc_types", {}).get(doc_type, {})
    doc_title = title if title is not None else info.get("title", "")
    pattern = info.get("name", "{title}.md")
    doc_file = pattern.replace("{title}", doc_title).replace("{period}", period).replace("{date}", str(as_of))
    return f"{cfg['paths']['documents']}/{doc_file}"


def md_table(headers: list[str], rows: list[list]) -> str:
    """A pipe table: '| a | b |', '|---|---|', one line per row, every cell through cell(). No rows gives one row whose first cell is 'None' and the rest empty (SKILL.md, Empty tables). Ends with a newline."""
    rows = rows or [["None"] + [""] * (len(headers) - 1)]
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def roster_names(root, cfg) -> dict[str, str]:
    """slug -> name from the roster register; {} when there is none."""
    try:
        entries = load_register(root, cfg, "roster")
    except ValueError:
        return {}
    return {r["slug"]: r["name"] for r in entries if isinstance(r, dict) and r.get("slug") and r.get("name")}


def person(value, names: dict[str, str]) -> str:
    """A slug, a list of slugs or free text as display text: slugs become names, other text is kept, lists are joined with ', ', empty is 'not set'."""
    if value is None or value == "" or value == []:
        return "not set"
    if isinstance(value, list):
        items = [names.get(x, str(x)) for x in value if x is not None and x != ""]
        return ", ".join(items) if items else "not set"
    if isinstance(value, str):
        val = value.strip()
        if not val:
            return "not set"
        return names.get(value, value)
    return names.get(str(value), str(value))


def statuses(cfg, register: str, key: str) -> list[str]:
    """registers.<register>.<key> (closed, blocked, active, pending) as a list; [] when absent."""
    reg = cfg.get("registers", {}).get(register, {}) if isinstance(cfg.get("registers"), dict) else {}
    if not isinstance(reg, dict):
        return []
    val = reg.get(key)
    if isinstance(val, list):
        return val
    if val is None:
        return []
    return [val]


def rag(cfg, as_of: datetime.date, tasks, milestones=(), issues=(), risks=()) -> tuple[str, str]:
    """(value from vocab.rag, one-line reason). The weekly-status rule:
    red   - a task of the top priority (vocab.priority_order[0]) is blocked or overdue; or a milestone is overdue;
            or three or more tasks are blocked or overdue
    amber - any task is blocked or overdue; or an open issue whose severity is one of the two last values of
            vocab.issue_severity; or an open risk whose impact is the last value of vocab.risk_level;
            or a milestone not closed and due within 7 days after as_of
    green - none of these
    overdue = not closed and due < as_of; blocked = status in registers.tasks.blocked.
    vocab.rag is read by position: [0] green, [1] amber, [2] red.
    The reason names the first rule that matched and up to three ids, e.g. 'top-priority task T-1 is overdue'."""
    rag_vocab = cfg.get("vocab", {}).get("rag") or ["green", "amber", "red"]
    green_val = rag_vocab[0]
    amber_val = rag_vocab[1] if len(rag_vocab) > 1 else "amber"
    red_val = rag_vocab[2] if len(rag_vocab) > 2 else "red"

    task_closed = statuses(cfg, "tasks", "closed")
    task_blocked = statuses(cfg, "tasks", "blocked")
    ms_closed = statuses(cfg, "milestones", "closed")
    issue_closed = statuses(cfg, "issues", "closed")
    risk_closed = statuses(cfg, "risks", "closed")

    def _safe_date(v):
        try:
            return to_date(v)
        except (ValueError, TypeError):
            return None

    def _is_overdue(e):
        d = _safe_date(e.get("due"))
        return d is not None and d < as_of

    prio_order = cfg.get("vocab", {}).get("priority_order") or []
    top_pri = prio_order[0] if prio_order else None

    def say(noun, ids, verb, rest):
        """'task T-1, T-2 are overdue': plural noun and verb when there is more than one id; at most three ids."""
        many = len(ids) > 1
        return f"{noun}{'s' if many else ''} {', '.join(str(x) for x in ids[:3])} {({'is': 'are', 'has': 'have'}[verb] if many else verb)} {rest}"

    def open_(t):
        return t.get("status") not in task_closed

    # Red rules
    # shortcut: direct list comprehensions kept over a shared helper to keep each rule explicit and avoid abstraction
    top = [t for t in tasks if top_pri is not None and t.get("priority") == top_pri and open_(t)]
    top_overdue = [t["id"] for t in top if _is_overdue(t)]
    if top_overdue:
        return red_val, say("top-priority task", top_overdue, "is", "overdue")
    top_blocked = [t["id"] for t in top if t.get("status") in task_blocked]
    if top_blocked:
        return red_val, say("top-priority task", top_blocked, "is", "blocked")

    ms_overdue = [m["id"] for m in milestones if m.get("status") not in ms_closed and _is_overdue(m)]
    if ms_overdue:
        return red_val, say("milestone", ms_overdue, "is", "overdue")

    all_bad_tasks = [t["id"] for t in tasks if open_(t) and (t.get("status") in task_blocked or _is_overdue(t))]
    if len(all_bad_tasks) >= 3:
        return red_val, f"3 or more tasks are blocked or overdue ({', '.join(str(x) for x in all_bad_tasks[:3])})"

    # Amber rules
    any_overdue = [t["id"] for t in tasks if open_(t) and _is_overdue(t)]
    if any_overdue:
        return amber_val, say("task", any_overdue, "is", "overdue")
    any_blocked = [t["id"] for t in tasks if open_(t) and t.get("status") in task_blocked]
    if any_blocked:
        return amber_val, say("task", any_blocked, "is", "blocked")

    issue_sev = cfg.get("vocab", {}).get("issue_severity") or []
    target_sev = set(issue_sev[-2:])
    bad_issues = [i["id"] for i in issues if i.get("status") not in issue_closed and i.get("severity") in target_sev]
    if bad_issues:
        return amber_val, say("open issue", bad_issues, "has", "high severity")

    risk_levels = cfg.get("vocab", {}).get("risk_level") or []
    target_risk = risk_levels[-1] if risk_levels else None
    bad_risks = [r["id"] for r in risks if target_risk is not None and r.get("status") not in risk_closed and r.get("impact") == target_risk]
    if bad_risks:
        return amber_val, say("open risk", bad_risks, "has", "high impact")

    soon_ms = [m["id"] for m in milestones if m.get("status") not in ms_closed
               and (d := _safe_date(m.get("due"))) is not None and as_of <= d <= as_of + datetime.timedelta(days=7)]
    if soon_ms:
        return amber_val, say("milestone", soon_ms, "is", "due within 7 days")

    return green_val, "all items on track"


def id_num(tid):
    """First number inside an id string, or 0 when there is none."""
    m = re.search(r"\d+", str(tid))
    return int(m.group()) if m else 0


def run(main):
    """Run a script's main(). An unexpected error prints one line and exits 2: 1 means findings."""
    try:
        return main()
    except Exception as e:
        if os.environ.get("PMO_DEBUG"):
            raise
        print(f"ERROR {Path(sys.argv[0]).name}: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
