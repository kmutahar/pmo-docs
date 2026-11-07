#!/usr/bin/env python3
"""Check that translations match their original documents (headings, tables, ids, numbers).

Usage:
    python3 parity_check.py [--project ROOT] [FILE ...]
"""
import sys

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

import argparse
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402
import structure_check as sc  # noqa: E402


def normalise(text: str, info: dict) -> str:
    """Digits in info['digits'] become 0-9. Characters in info['separators'] become '.'. A connector word from info['connectors'], or of, to, and, or one of / : - en dash, em dash, between two numbers becomes '~'. Ids are not touched here."""
    info = info or {}
    digits = info.get("digits")
    if isinstance(digits, str) and len(digits) == 10:
        text = text.translate({ord(ch): str(i) for i, ch in enumerate(digits)})  # one pass: a digit set that reuses 0-9 stays correct

    separators = info.get("separators")
    if isinstance(separators, str):
        text = text.translate({ord(ch): "." for ch in separators})

    # Punctuation connectors between two digits
    text = re.sub(r"(?<=\d)\s*[-/:\u2013\u2014]\s*(?=\d)", "~", text)

    # Word connectors between two digits
    words = {"of", "to", "and"}
    conn = info.get("connectors")
    if isinstance(conn, dict):
        for v in conn.values():
            if isinstance(v, str) and v.strip():
                words.add(v.strip())
    elif isinstance(conn, (list, tuple)):
        for v in conn:
            if isinstance(v, str) and v.strip():
                words.add(v.strip())
    elif isinstance(conn, str) and conn.strip():
        words.add(conn.strip())

    words_pat = "|".join(re.escape(w) for w in sorted(words, key=lambda w: -len(w)))
    text = re.sub(r"(?<=\d)\s+(?:" + words_pat + r")\s+(?=\d)", "~", text, flags=re.IGNORECASE)
    return text


def id_regex(cfg) -> re.Pattern:
    """Ids from the register prefixes in the config: (?<![A-Za-z0-9])(?:T|P|...)-\\d+ ; the lookbehind, not \\b, so an id glued to a letter of another script still matches."""
    regs = cfg.get("registers", {}) if isinstance(cfg, dict) else {}
    prefixes = [r["prefix"] for r in regs.values() if isinstance(r, dict) and r.get("prefix")]
    if not prefixes:
        prefixes = ["T", "P", "M", "R", "I", "A", "D", "DEC", "CR", "ACT", "MTG", "TM"]
    prefixes = sorted(set(prefixes), key=lambda x: (-len(x), x))
    pat = r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(p) for p in prefixes) + r")-\d+"
    return re.compile(pat)


def numbers(text: str, info: dict, idrx) -> list[str]:
    """Number phrases in order: ids are removed first, then normalise(), then runs like 2026~03~15, 3~5, 25, 3.5. A percent sign is ignored."""
    text = idrx.sub("", text)
    text = text.replace("%", "").replace("\u066a", "")
    norm = normalise(text, info)
    return re.findall(r"\d+(?:[.~]\d+)*", norm)


def text_outside_tables(text: str) -> str:
    """Lines of text that do not belong to Markdown tables."""
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        if i < len(lines) - 1 and lines[i].lstrip().startswith("|") and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                i += 1
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def compare(original: str, translation: str, info: dict, cfg) -> list[str]:
    """Differences, [] when they match. Uses structure_check.sections and structure_check.tables."""
    errors = []
    idrx = id_regex(cfg)
    draft_lang = pc.languages(cfg)["draft"] if cfg else "en"
    draft_info = pc.languages(cfg)["info"].get(draft_lang, {}) if cfg else {}

    orig_fm, orig_body = pc.split_front_matter(original)
    trans_fm, trans_body = pc.split_front_matter(translation)
    orig_fm = orig_fm or {}
    trans_fm = trans_fm or {}

    # 1. Front matter: type equal; period and template_version equal when original has them
    if orig_fm.get("type") != trans_fm.get("type"):
        errors.append(f"front matter type `{trans_fm.get('type')}` differs from original `{orig_fm.get('type')}`")
    if "period" in orig_fm and orig_fm.get("period") != trans_fm.get("period"):
        errors.append(f"front matter period `{trans_fm.get('period')}` differs from original `{orig_fm.get('period')}`")
    if "template_version" in orig_fm and orig_fm.get("template_version") != trans_fm.get("template_version"):
        errors.append(f"front matter template_version `{trans_fm.get('template_version')}` differs from original `{orig_fm.get('template_version')}`")

    orig_sec = sc.sections(orig_body)
    trans_sec = sc.sections(trans_body)

    # 2. Headings: same count; same level at each position
    if len(orig_sec) != len(trans_sec):
        errors.append(f"heading count differs: original has {len(orig_sec)}, translation has {len(trans_sec)}")
        otabs = sum(len(sc.tables(s[2])) for s in orig_sec)
        ttabs = sum(len(sc.tables(s[2])) for s in trans_sec)
        if otabs != ttabs:
            errors.append(f"total table count differs: original has {otabs}, translation has {ttabs}")
        return errors

    for (olv, otitle, _), (tlv, _, _) in zip(orig_sec, trans_sec):
        if olv != tlv:
            errors.append(f"`{otitle}`: heading level {tlv} differs from original level {olv}")

    # 3. For each aligned section
    for (olv, otitle, otext), (tlv, ttitle, ttext) in zip(orig_sec, trans_sec):
        otabs = sc.tables(otext)
        ttabs = sc.tables(ttext)
        if len(otabs) != len(ttabs):
            errors.append(f"`{otitle}`: table count differs: original has {len(otabs)}, translation has {len(ttabs)}")
        else:
            for t_idx, ((ohead, orows), (thead, trows)) in enumerate(zip(otabs, ttabs), 1):
                if len(ohead) != len(thead):
                    errors.append(f"`{otitle}` table {t_idx}: column count differs: {len(thead)} != {len(ohead)}")
                if len(orows) != len(trows):
                    errors.append(f"`{otitle}` table {t_idx}: rows count differs: {len(trows)} != {len(orows)}")
                if len(ohead) != len(thead) or len(orows) != len(trows):
                    continue  # cells cannot be paired; the shape message is enough
                for c_idx, (ohc, thc) in enumerate(zip(ohead, thead), 1):
                    on = numbers(ohc, draft_info, idrx)
                    tn = numbers(thc, info, idrx)
                    if on != tn:
                        errors.append(f"`{otitle}` table {t_idx} header cell {c_idx}: numbers differ: {tn} != {on}")
                for r_idx, (orow, trow) in enumerate(zip(orows, trows), 1):
                    for c_idx, (oc, tc) in enumerate(zip(orow, trow), 1):
                        on = numbers(oc, draft_info, idrx)
                        tn = numbers(tc, info, idrx)
                        if on != tn:
                            errors.append(f"`{otitle}` table {t_idx} row {r_idx} cell {c_idx}: numbers differ: {tn} != {on}")

        oids = sorted(idrx.findall(f"{otitle}\n{otext}"))
        tids = sorted(idrx.findall(f"{ttitle}\n{ttext}"))
        if oids != tids:
            errors.append(f"`{otitle}`: ids differ: {tids} != {oids}")

        onums = sorted(numbers(f"{otitle}\n{text_outside_tables(otext)}", draft_info, idrx))
        tnums = sorted(numbers(f"{ttitle}\n{text_outside_tables(ttext)}", info, idrx))
        if onums != tnums:
            errors.append(f"`{otitle}`: numbers differ: {tnums} != {onums}")

    return errors


def check_translation(root, cfg, path) -> list[str]:
    """Reads the translation, finds its original through translation_of (relative to paths.documents), looks up pc.languages(cfg)['info'][lang], and returns compare(...). An unreadable pair gives one message: no translation_of, original missing, lang not in the config, translation_of leaving paths.documents."""
    path = Path(path)
    if not path.is_file():
        return [f"file not found: {path}"]
    text = pc.read(path)
    fm, _ = pc.split_front_matter(text)
    if fm is None or not fm.get("translation_of"):
        return ["no translation_of in front matter"]

    rel_orig = fm.get("translation_of")
    if not isinstance(rel_orig, str):
        return ["translation_of must be a string"]

    docs_folder = Path(root) / cfg["paths"]["documents"]
    if pc.outside(docs_folder, rel_orig):
        return [f"translation_of `{rel_orig}` leaves paths.documents"]

    orig_file = docs_folder / rel_orig
    if not orig_file.is_file():
        return [f"original `{rel_orig}` missing"]

    lang = fm.get("lang")
    if not lang or not isinstance(lang, str):
        return ["lang missing in front matter"]

    langs = pc.languages(cfg)
    if lang not in langs["info"]:
        return [f"lang `{lang}` not in config"]

    info = langs["info"][lang]
    orig_text = pc.read(orig_file)
    return compare(orig_text, text, info, cfg)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check that translations match their original documents.")
    pc.add_project_arg(ap)
    ap.add_argument("files", nargs="*", help="translation files to check (default: all files with translation_of under paths.documents)")
    a = ap.parse_args(argv)
    root = Path(a.project).resolve()
    if not root.is_dir():
        ap.error(f"project folder not found: {a.project}")
    cfg = pc.load_config(root)
    if bad := render_views.config_errors(cfg, root=root):
        print("\n".join("ERROR " + e for e in bad), file=sys.stderr)
        return 2

    docs_dir = root / cfg["paths"]["documents"]
    if a.files:
        files = [Path(f) if Path(f).is_absolute() else (Path.cwd() / f).resolve() for f in a.files]
    else:
        files = []
        if docs_dir.is_dir():
            for f in sorted(docs_dir.rglob("*.md")):
                try:
                    fm, _ = pc.split_front_matter(pc.read(f))
                    if fm and "translation_of" in fm:
                        files.append(f)
                except Exception:
                    pass

    bad = 0
    for f in files:
        if not f.is_file():
            print(f"ERROR {f}: not a file")
            bad += 1
            continue
        rel = f.resolve().relative_to(root) if root in f.resolve().parents else f
        errors = check_translation(root, cfg, f)
        if errors:
            print("\n".join(f"ERROR {rel}: {e}" for e in errors))
            bad += 1
        else:
            print(f"ok    {rel}")

    print(f"\n{bad} file(s) differ from their originals")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
