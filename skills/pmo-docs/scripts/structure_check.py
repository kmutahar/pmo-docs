#!/usr/bin/env python3
"""Check that documents keep the structure of their template (the template is the contract).

Usage:
    python3 structure_check.py [--project ROOT] [FILE ...]   # default: every .md under paths.documents

Translations (front matter `translation_of`) are checked lightly: keys, title, placeholders, comments, duplicate IDs; parity_check compares their structure.

A document's type is its front-matter `type`. The template is found like `where.py` does it
(pmo/templates/<name> in the project wins over the skill's default), and the checks come from
that template only, never from the draft.

Always checked, from the template:
  ERROR  front-matter key missing (except `checks`), or `type` unknown; front matter not valid YAML
  ERROR  a required heading is missing or out of order (the `#` title is free; a heading that
         starts with {{x}} is an optional repeatable slot; {{x}} inside other words matches any words)
  ERROR  a table's columns differ from the template's table in that section
  ERROR  an unreplaced {{placeholder}} or any HTML comment left in the text
  ERROR  the same ID (T-001) twice in one table
  WARN   no front matter; template_version missing or different; extra `##` sections; empty table

Declared checks: the template's front matter may carry a `checks:` list. A section is named by its
heading text (case-insensitive, no markup); it covers the heading and everything below it. A check
that names a section the document lacks FAILS (so a renamed heading is caught). A row whose only
filled cell is "None" is exempt. Kinds:

  - kind: required_cells          # these columns must be filled in every row of the section's tables
    section: Risks
    columns: [Owner, Status]

  - kind: equal_count             # table rows in one section == headings of one level in another
    rows_in: Decision index
    headings_in: Decisions
    level: 3                      # number of '#'

  - kind: listed_have_sections    # each first-column entry of the list has a heading (prefix match)
    listed_in: Risks at a glance
    sections_in: Risks
    level: 3

Exit codes: 0 clean (warnings allowed), 1 findings, 2 usage (including a project folder that does not exist).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402


def sections(body):
    """[(level, title, text until the next heading)] in order; code fences and HTML comments ignored."""
    body = re.sub(r"<!--.*?-->", "", re.sub(r"```.*?```", "", body, flags=re.S), flags=re.S)
    out = []
    for line in body.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            out.append([len(m.group(1)), m.group(2), []])
        elif out:
            out[-1][2].append(line)
    return [(lv, t, "\n".join(txt)) for lv, t, txt in out]


def row_cells(line):
    s = line.strip()[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def tables(text):
    """[(header cells, [row cells])] for every Markdown table in text."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head, rows, i = row_cells(lines[i]), [], i + 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(row_cells(lines[i]))
                i += 1
            out.append((head, rows))
        else:
            i += 1
    return out


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", s)).strip().lower()


def is_none_row(row):
    full = [c for c in row if c]
    return len(full) == 1 and full[0].strip("_*. ").lower() == "none"


def heading_rx(title):
    """Regex for a template heading; each {{x}} matches any words."""
    parts = re.split(r"\{\{.*?\}\}", norm(title))
    return re.compile(r"\A" + ".+".join(re.escape(p) for p in parts) + r"\Z")


def is_slot(title):
    bare = re.sub(r"\{\{.*?\}\}", "", title)
    return title.strip().startswith(("{{", "`{{")) or not re.search(r"\w", bare)


def span(dsec, name):
    """The named section and the sections below it, or None when the document has no such heading."""
    for i, (lv, t, _) in enumerate(dsec):
        if norm(t) == norm(name):
            j = i + 1
            while j < len(dsec) and dsec[j][0] > lv:
                j += 1
            return dsec[i:j]
    return None


def data_rows(sp):
    return [r for s in sp for _, rows in tables(s[2]) for r in rows if not is_none_row(r)]


def run_checks(checks, dsec):
    """Errors from the template's declared checks, run on the document's sections."""
    errors = []
    for n, c in enumerate(checks or [], 1):
        kind, tag = c.get("kind") if isinstance(c, dict) else None, f"template check {n}"
        need = {"required_cells": ("section", "columns"), "equal_count": ("rows_in", "headings_in", "level"),
                "listed_have_sections": ("listed_in", "sections_in", "level")}.get(kind)
        if not need or any(k not in c for k in need):
            errors.append(f"{tag}: unknown kind or missing keys (kind {kind!r}, needs {need})")
            continue
        names = [c[k] for k in need if k in ("section", "rows_in", "headings_in", "listed_in", "sections_in")]
        spans = {nm: span(dsec, nm) for nm in names}
        gone = [nm for nm, sp in spans.items() if sp is None]
        if gone:
            errors.append(f"{tag} ({kind}): section `{gone[0]}` not found (renamed or removed?)")
            continue
        if kind == "required_cells":
            tabs = [t for s in spans[c["section"]] for t in tables(s[2])]
            if not tabs:
                errors.append(f"`{c['section']}`: no table found")
            for head, rows in tabs:
                h = [norm(x) for x in head]
                for col in c["columns"]:
                    if norm(col) not in h:
                        errors.append(f"`{c['section']}`: column `{col}` missing")
                        continue
                    i = h.index(norm(col))
                    for r in rows:
                        if not is_none_row(r) and (i >= len(r) or not r[i]):
                            errors.append(f"`{c['section']}` row `{r[0] or '?'}`: {col} empty (write \"not set\" + open question)")
        elif kind == "equal_count":
            rows = len(data_rows(spans[c["rows_in"]]))
            heads = sum(1 for lv, _, _ in spans[c["headings_in"]] if lv == c["level"])
            if rows != heads:
                errors.append(f"`{c['rows_in']}` has {rows} rows but `{c['headings_in']}` has {heads} level-{c['level']} headings (must be equal)")
        else:
            heads = [norm(t) for lv, t, _ in spans[c["sections_in"]] if lv == c["level"]]
            for r in data_rows(spans[c["listed_in"]]):
                x = norm(r[0]) if r and r[0] else ""
                if x and not any(x.startswith(y) or y.startswith(x) for y in heads):
                    errors.append(f"`{c['sections_in']}` has no level-{c['level']} heading for `{r[0]}` (listed in `{c['listed_in']}`)")
    return errors


def duplicate_ids(text):
    dups = set()
    for _, rows in tables(re.sub(r"```.*?```", "", text, flags=re.S)):
        seen = set()
        for r in rows:
            cell = r[0].strip("`") if r else ""  # ids may be written as `DEC-1`
            if re.fullmatch(r"[A-Z]{1,4}-\d+[A-Za-z]?", cell):
                (dups if cell in seen else seen).add(cell)
    return sorted(dups)


def check_head(tfm, fm, errors, warns):
    """Front-matter keys the template has, and its template_version."""
    errors += [f"front matter key `{k}` missing" for k in tfm if k != "checks" and k not in fm]
    tv, dv = tfm.get("template_version"), fm.get("template_version")
    if tv is not None and dv != tv:
        warns.append(f"template_version {dv} differs from template v{tv}" if dv is not None else f"no template_version (template is v{tv})")


def check_tail(text, body, errors):
    """Placeholders, HTML comments and duplicate ids left in a document."""
    if re.search(r"\{\{.*?\}\}", re.sub(r"```.*?```", "", text, flags=re.S)):
        errors.append("unreplaced {{placeholder}} left in text")
    if "<!--" in body:
        errors.append("HTML comment `<!--` left in document (remove template/author notes)")
    if dups := duplicate_ids(body):
        errors.append("duplicate IDs in one table: " + ", ".join(dups[:8]))


def check_translation_light(tfm, fm, text, body):
    """(errors, warnings) for a translation document (light check)."""
    errors, warns = [], []
    check_head(tfm or {}, fm, errors, warns)
    dsec = sections(body)
    if sum(1 for lv, _, _ in dsec if lv == 1) != 1:
        errors.append("document must have exactly one `#` title")
    check_tail(text, body, errors)
    return errors, warns


def check(root, cfg, text):
    """(errors, warnings) for one document's text."""
    errors, warns = [], []
    try:
        fm, body = pc.split_front_matter(text, strict=True)
    except pc.yaml.YAMLError as ex:
        return [f"front matter is not valid YAML ({str(ex).splitlines()[0]}); quote values with {{{{ }}}} or ':'"], warns
    if fm is None:
        return errors, ["no front matter (no type, so no template to check against)"]
    tid = fm.get("type")
    dt = cfg["doc_types"].get(tid) if isinstance(tid, str) else None
    if not dt:
        return [f"front matter type `{tid}` is not a doc type in the config"], warns
    try:
        tpl, _ = pc.find_asset(root, cfg, "templates", dt.get("template", f"{tid}.md"))
    except ValueError as e:
        return [str(e)], warns
    if not tpl.exists():
        return [f"template {dt.get('template', f'{tid}.md')} not found"], warns
    try:
        tfm, tbody = pc.split_front_matter(pc.read(tpl), strict=True)
    except pc.yaml.YAMLError:
        return [f"template {dt.get('template', f'{tid}.md')}: template front matter invalid"], warns
    tfm = tfm or {}
    if fm.get("translation_of") is not None:
        return check_translation_light(tfm, fm, text, body)
    check_head(tfm, fm, errors, warns)

    tsec, dsec = sections(tbody), sections(body)
    if sum(1 for lv, _, _ in dsec if lv == 1) != 1:
        errors.append("document must have exactly one `#` title")
    pos = -1
    for lv, title, ttext in tsec:
        if lv == 1 or is_slot(title):
            continue
        rx = heading_rx(title)
        hit = lambda i, d: d[0] == lv and rx.match(norm(d[1]))
        idx = next((i for i, d in enumerate(dsec) if i > pos and hit(i, d)), None)
        if idx is None:
            errors.append(f"heading `{'#' * lv} {title}` " + ("is out of order" if any(hit(i, d) for i, d in enumerate(dsec)) else "is missing"))
            continue
        pos = idx
        tt, dt_ = tables(ttext), tables(dsec[idx][2])
        if tt:
            if not dt_:
                errors.append(f"`{title}`: table with columns {tt[0][0]} is missing")
            elif [norm(c) for c in dt_[0][0]] != [norm(c) for c in tt[0][0]]:
                errors.append(f"`{title}`: table columns {dt_[0][0]} should be {tt[0][0]}")
    rxs = [(lv, heading_rx(t)) for lv, t, _ in tsec]
    extra = [t for lv, t, _ in dsec if lv == 2 and not any(l == lv and r.match(norm(t)) for l, r in rxs)]
    if extra:
        warns.append("extra sections: " + "; ".join(extra[:6]) + (" ..." if len(extra) > 6 else ""))
    warns += [f"`{t}`: empty table (keep the header and add one row: None)" for lv, t, txt in dsec if lv == 2 for _, rows in tables(txt) if not rows]

    check_tail(text, body, errors)
    return errors + run_checks(tfm.get("checks"), dsec), warns


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check documents against their template's structure and declared checks.")
    pc.add_project_arg(ap)
    ap.add_argument("files", nargs="*", help="documents to check (default: every .md under paths.documents)")
    a = ap.parse_args(argv)
    root = Path(a.project).resolve()
    if not root.is_dir():
        ap.error(f"project folder not found: {a.project}")
    cfg = pc.load_config(root)
    files = [Path(f) for f in a.files] or sorted((root / cfg["paths"]["documents"]).rglob("*.md"))
    bad = 0
    for f in files:
        if not f.is_file():
            print(f"ERROR {f}: not a file")
            bad += 1
            continue
        errors, warns = check(root, cfg, pc.read(f))
        rel = f.resolve().relative_to(root) if root in f.resolve().parents else f
        print("\n".join([f"ERROR {rel}: {e}" for e in errors] + [f"warn  {rel}: {w}" for w in warns]) or f"ok    {rel}")
        bad += bool(errors)
    print(f"\n{bad} file(s) with structure errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
