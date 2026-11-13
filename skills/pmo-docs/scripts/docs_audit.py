#!/usr/bin/env python3
"""Mechanical documentation audit. Prints a Markdown report, exits 1 when there are findings
(2 for a usage error, including a project folder that does not exist).

Usage:
    python3 docs_audit.py [--project ROOT] [--as-of YYYY-MM-DD]

Walks the documents folder (paths.documents). A document's type is its front-matter `type` and must
be a doc type in the config. Checks:
  front matter  `type` is present and is a known doc type
  stale         a document with `status: finished` is stale when the hash recorded in its front matter for any
                register in the type's `generated_from` differs from the register's current hash
  translation behind a finished translation whose source_hash differs from body_hash of its original
  parity        a translation differing in headings, tables, ids, numbers, list items and ticked boxes from its original
  old           a finished document is older than its type's `stale_days` (front-matter
                `last_updated`; a finished document without it is a front-matter finding)
  broken links  relative Markdown links that point at a missing file

Recorded hashes (written by the Finish step) live in front matter as
    source_hashes: {tasks: "ab12cd34", risks: "0f9e8d7c"}
Each value is the first 8 hex characters of the SHA-256 of the register file's bytes, with CRLF
line endings read as LF (see register_hash); a register file that does not exist hashes to "none".
Quote the values: an
all-digit hash such as 12345678 would be read as a number and is reported as "quote the hash".
Docs-vs-code drift is not mechanical: the docs-audit playbook covers it.
"""
import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parity_check as pcheck  # noqa: E402
import pmo_common as pc  # noqa: E402


def _unquote(s):
    """Decode %XX escapes in a link target (UTF-8)."""
    return re.sub(r"(?:%[0-9A-Fa-f]{2})+", lambda m: bytes.fromhex(m[0].replace("%", "")).decode("utf-8", "replace"), s)


CHECKS = ("front matter", "stale", "old", "broken links", "override drift", "translation behind", "parity")
STALE_CHECKS = ("stale", "translation behind")


def register_hash(root, cfg, name):
    """8 hex characters of the SHA-256 of a register's file (with CRLF line endings read as LF), or "none" when the file is missing."""
    f = Path(root) / cfg["paths"]["registers"] / cfg["registers"][name]["file"]
    return hashlib.sha256(f.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:8] if f.exists() else "none"


def audit_translation(root, cfg, path, base, fm, text) -> list[tuple[str, str]]:
    """Findings for one translation. All 'front matter' unless named."""
    rel = path.relative_to(base)
    out = []

    trans_of = fm.get("translation_of")
    if not isinstance(trans_of, str) or not trans_of.strip():
        return [("front matter", f"`{rel}` - translation_of does not name a document")]

    p_trans = Path(trans_of)
    if p_trans.is_absolute() or ".." in p_trans.parts or pc.outside(base, trans_of):
        return [("front matter", f"`{rel}` - translation_of does not name a document")]

    orig_path = (base / trans_of).resolve()
    if not orig_path.is_file():
        return [("front matter", f"`{rel}` - translation_of does not name a document")]

    try:
        orig_text = pc.read(orig_path)
    except UnicodeDecodeError:
        return [("front matter", f"`{rel}` - the original is not UTF-8 text")]
    orig_fm, _ = pc.split_front_matter(orig_text)
    orig_fm = orig_fm or {}

    if "translation_of" in orig_fm:
        return [("front matter", f"`{rel}` - the original is itself a translation")]

    trans_langs = pc.languages(cfg).get("translations", [])
    lang = fm.get("lang")
    if not lang or not isinstance(lang, str) or lang not in trans_langs:
        out.append(("front matter", f"`{rel}` - lang {lang} is not a translation language in the config"))

    ty = fm.get("type")
    if isinstance(ty, str) and isinstance(lang, str) and lang in trans_langs:
        if lang not in pc.type_translations(cfg, ty):
            out.append(("front matter", f"`{rel}` - type {ty} is not translated into {lang}"))

    if isinstance(lang, str) and not path.name.endswith(f".{lang}.md"):
        out.append(("front matter", f"`{rel}` - the file name should end in .{lang}.md"))

    if isinstance(lang, str) and lang in trans_langs:
        expected_dir = pc.languages(cfg)["info"].get(lang, {}).get("dir")
        if fm.get("dir") != expected_dir:
            out.append(("front matter", f"`{rel}` - dir should be {expected_dir}"))

    if fm.get("type") != orig_fm.get("type"):
        out.append(("front matter", f"`{rel}` - type differs from the original"))

    if "source_hashes" in fm:
        out.append(("front matter", f"`{rel}` - translations record source_hash, not source_hashes"))

    sh = fm.get("source_hash")
    if sh is None or not isinstance(sh, str):
        out.append(("front matter", f"`{rel}` - source_hash is missing or not quoted text"))

    is_finished = fm.get("status") == "finished"
    orig_finished = orig_fm.get("status") == "finished"
    if is_finished and not orig_finished:
        out.append(("front matter", f"`{rel}` - finished, but its original is not finished"))

    if is_finished and isinstance(sh, str):
        if pc.body_hash(orig_text) != sh:
            out.append(("translation behind", f"`{rel}` - translation behind its original: the original changed since it was translated"))

    if isinstance(lang, str) and lang in pc.languages(cfg)["info"]:
        parity_messages = pcheck.compare(orig_text, text, pc.languages(cfg)["info"][lang], cfg)
        for msg in parity_messages:
            out.append(("parity", f"`{rel}` - {msg}"))

    return out


def audit_file(root, cfg, path, base, today):
    """[(check, message)] for one document."""
    rel = path.relative_to(base)
    out = []
    try:
        text = pc.read(path)
    except UnicodeDecodeError:
        return [("front matter", f"`{rel}` - not UTF-8 text")]
    try:
        fm, _ = pc.split_front_matter(text, strict=True)
    except pc.yaml.YAMLError as e:
        lines = str(e).splitlines()
        first_line = lines[0] if lines else str(e)
        return [("front matter", f"`{rel}` - front matter is not valid YAML ({first_line})")]
    if fm is None:
        return [("front matter", f"`{rel}` - no front matter")]
    ty = fm.get("type")
    if not ty:
        out.append(("front matter", f"`{rel}` - front matter has no `type`"))
    t = cfg["doc_types"].get(ty) if isinstance(ty, str) else None
    if ty and not t:
        out.append(("front matter", f"`{rel}` - type `{fm['type']}` is not a doc type in the config"))
    if "status" in fm and fm["status"] not in ("draft", "finished"):
        bad_status = fm["status"]
        out.append(("front matter", f"`{rel}` - status `{bad_status}` is not draft or finished"))
    if "translation_of" in fm:
        out.extend(audit_translation(root, cfg, path, base, fm, text))
    else:
        if t and fm.get("status") == "finished":
            recorded = fm.get("source_hashes") or {}
            if not isinstance(recorded, dict):
                out.append(("front matter", f"`{rel}` - source_hashes must be a map of register to hash"))
                recorded = {}
            for reg in t.get("generated_from") or []:
                if reg not in cfg["registers"]:
                    continue
                if reg not in recorded:
                    out.append(("stale", f"`{rel}` - no recorded hash for register `{reg}`"))
                elif not isinstance(recorded[reg], str):
                    out.append(("front matter", f"`{rel}` - recorded hash for register `{reg}` is not text: quote the hash"))
                elif recorded[reg] != register_hash(root, cfg, reg):
                    out.append(("stale", f"`{rel}` - register `{reg}` changed since the document was finished"))
            try:
                stamp = pc.to_date(fm.get("last_updated"))
            except ValueError:
                stamp = None
                out.append(("front matter", f"`{rel}` - last_updated is not a YYYY-MM-DD date"))
            else:
                if stamp is None:
                    out.append(("front matter", f"`{rel}` - finished but has no `last_updated`"))
            if stamp and t.get("stale_days") and (today - stamp).days > t["stale_days"]:
                out.append(("old", f"`{rel}` - {(today - stamp).days} days old (limit {t['stale_days']})"))
        elif t and fm.get("status") == "draft":
            recorded = fm.get("source_hashes")
            if isinstance(recorded, dict):
                for reg in t.get("generated_from") or []:
                    if reg not in cfg["registers"]:
                        continue
                    if reg in recorded and recorded[reg] != register_hash(root, cfg, reg):
                        out.append(("stale", f"`{rel}` - draft is behind: register `{reg}` changed since the draft was made"))
    unfenced = re.sub(r"^ {0,3}(```|~~~).*?^ {0,3}\1[^\n]*$", "", text, flags=re.S | re.M)  # links in fenced code are examples
    cleaned = re.sub(r"(`+)[^\n]+?\1", "", unfenced)
    for m in re.finditer(r"""\]\(\s*(?:<([^>\n]*)>|([^)\s]+))(?:\s+(?:"[^"\n]*"|'[^'\n]*'))?\s*\)""", cleaned):
        target = m.group(1) if m.group(1) is not None else m.group(2)
        if not target or target.startswith(("#", "/")) or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            continue
        if not (path.parent / _unquote(target.split("#")[0])).exists():
            out.append(("broken links", f"`{rel}` -> `{target}`"))
    return out


def _drift(rel_str: str, own_fm: dict | None, default_fm: dict | None, version_key: str, expected_name: str, kind: str) -> str | None:
    own_fm = own_fm or {}
    default_fm = default_fm or {}
    default_ver = default_fm.get(version_key)
    if not isinstance(default_ver, int):
        default_ver = 1

    raw_based_on = own_fm.get("based_on")
    if raw_based_on is None or raw_based_on == "":
        return f"`{rel_str}` - no based_on; add based_on: {expected_name}@{default_ver} after comparing with the default"

    val_str = str(raw_based_on).strip()
    m = re.match(r"^([^@]+)@(\d+)$", val_str)
    if not m:
        return f"`{rel_str}` - based_on {val_str} is not <type>@<number>"

    name, ver_str = m.group(1).strip(), m.group(2)
    if name != expected_name:
        return f"`{rel_str}` - based_on names {name}, the default is {expected_name}"

    own_ver = int(ver_str)
    if own_ver < default_ver:
        return f"`{rel_str}` - the default {kind} moved from v{own_ver} to v{default_ver}; compare them, then raise based_on"
    if own_ver > default_ver:
        return f"`{rel_str}` - based_on v{own_ver} is newer than the default (v{default_ver})"

    return None


def _template_msg(rel_str, own_file, default_file):
    own_fm = pc.split_front_matter(pc.read(own_file))[0]
    def_fm = pc.split_front_matter(pc.read(default_file))[0]
    expected_type = (def_fm or {}).get("type") or own_file.stem
    return _drift(rel_str, own_fm, def_fm, "template_version", expected_type, "template")


def template_drift(root, cfg) -> list[str]:
    """One message per project template in paths.templates whose default (same file name in the skill's
    assets/templates) exists and whose based_on is missing, malformed, names another type, or has a version
    below the default's template_version. A project template with no default is skipped."""
    base = Path(root) / cfg["paths"]["templates"]
    if not base.exists():
        return []
    out = []
    for p in sorted(base.rglob("*.md")):
        rel = p.relative_to(base)
        default_file = pc.SKILL / "assets" / "templates" / rel.name
        if not default_file.exists():
            continue
        try:
            msg = _template_msg(str(rel), p, default_file)
        except UnicodeDecodeError:
            msg = f"`{rel}` - not UTF-8 text"
        if msg:
            out.append(msg)
    return out


def playbook_drift(root, cfg) -> list[str]:
    """One message per project playbook in paths.playbooks whose default exists in references and has drift."""
    playbooks_path = cfg["paths"].get("playbooks")
    if not playbooks_path:
        return []
    base = Path(root) / playbooks_path
    if not base.exists():
        return []
    out = []
    for p in sorted(base.rglob("*.md")):
        rel = p.relative_to(base)
        default_file = pc.SKILL / "references" / rel
        if not default_file.exists():
            continue
        try:
            own_fm = pc.split_front_matter(pc.read(p))[0]
            def_fm = pc.split_front_matter(pc.read(default_file))[0]
        except UnicodeDecodeError:
            out.append(f"`{rel.as_posix()}` - not UTF-8 text")
            continue
        expected_name = rel.with_suffix("").as_posix()
        msg = _drift(rel.as_posix(), own_fm, def_fm, "playbook_version", expected_name, "playbook")
        if msg:
            out.append(msg)
    return out


def drift_state(root, cfg, tpl_path: Path, tpl_source: str) -> str:
    """Return 'yes' | 'no' | 'n/a' for a template's drift status."""
    if tpl_source != "project":
        return "n/a"
    default_file = pc.SKILL / "assets" / "templates" / tpl_path.name
    if not default_file.exists():
        return "n/a"
    return "yes" if _template_msg(tpl_path.name, tpl_path, default_file) else "no"


def audit(root, cfg, today):
    """(files scanned, {check: [message]})."""
    base = Path(root) / cfg["paths"]["documents"]
    files = sorted(base.rglob("*.md")) if base.exists() else []
    found = {c: [] for c in CHECKS}
    for p in files:
        for check, msg in audit_file(root, cfg, p, base, today):
            found[check].append(msg)
    t_drift = template_drift(root, cfg)
    p_drift = playbook_drift(root, cfg)
    found["override drift"].extend(t_drift + p_drift)
    return len(files), found


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mechanical documentation audit; exits 1 on findings.")
    pc.add_project_arg(ap)
    ap.add_argument("--as-of", type=datetime.date.fromisoformat, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date used for age checks (default: today)")
    args = ap.parse_args(argv)
    if not Path(args.project).is_dir():
        ap.error(f"project folder not found: {args.project}")
    cfg = pc.load_config(args.project)
    count, found = audit(args.project, cfg, args.as_of)
    print(f"# Docs audit - {args.as_of}\n\nScanned {count} Markdown files.\n")
    total = 0
    for check, items in found.items():
        total += len(items)
        print(f"## {check.capitalize()} ({len(items)})\n")
        print("\n".join(f"- {x}" for x in items) if items else "None")
        print()
    print(f"**Total findings: {total}**")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
