"""Shared translation test fixture. Invented language 'xx' for Acme 'Decision log.md'."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True  # importing the shipped scripts must leave no __pycache__
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402

WORDS = {
    "Host on shared cloud": "Hostar sur nubia",
    "Use weekly releases": "Usar livrationes hebdomadales",
    "Open questions": "Questiones apertas",
    "Use the shared cloud account": "Usar computum nubis",
    "Release every Thursday": "Livrar omni die jovis",
    "Need cheap hosting": "Besoing hospitatione barata",
    "Team wants steady delivery": "Equipa vol livraison constante",
    "Options considered": "Optiones consideratas",
    "Supersedes / related": "Supersedex et relato",
    "Decided by": "Decidat per",
    "Lower cost": "Costo minor",
    "Smaller changes": "Mutationes minores",
    "shared, own": "partito, proprio",
    "weekly, monthly": "hebdomadal, mensual",
    "None yet.": "Nulla ancora.",
    "Summary": "Sumariox",
    "Decisions": "Decisiones",
    "Decision": "Decisioba",
    "Status": "Statux",
    "Date": "Datox",
    "Context": "Contexto",
    "Consequences": "Consequentias",
    "proposed": "proposito",
    "accepted": "acceptato",
    "none": "nulla",
}


def strip_languages_block(cfg_text: str) -> str:
    """Remove any top-level languages block from config.yaml text without changing other sections."""
    lines = cfg_text.splitlines(keepends=True)
    out = []
    skipping = False
    for line in lines:
        if skipping:
            if line.strip() == "" or line.startswith((" ", "\t", "#")):
                continue
            skipping = False
        if line.startswith("languages:"):
            skipping = True
            continue
        out.append(line)
    return "".join(out)


def enable_languages(project: Path, translations=("xx",), block: str = "") -> None:
    """Write a languages block to project/pmo/config.yaml (replacing any existing block): draft en, the given translations with label and dir rtl, plus the extra YAML in block (for example a digits line)."""
    cfg_file = Path(project) / "pmo/config.yaml"
    base = strip_languages_block(cfg_file.read_text(encoding="utf-8"))
    if base and not base.endswith("\n"):
        base += "\n"
    text = (
        "\nlanguages:\n"
        "  draft: en\n"
        f"  translations: [{', '.join(translations)}]\n"
        "  en:\n"
        "    label: EN\n"
        "    dir: ltr\n"
    )
    for t in translations:
        text += f"  {t}:\n    label: {t.upper()}\n    dir: rtl\n"
    if block:
        if not block.endswith("\n"):
            block += "\n"
        text += block
    cfg_file.write_text(base + text, encoding="utf-8")
    if "ar" not in translations:
        ar_doc = Path(project) / "pmo/documents/Decision log.ar.md"
        if ar_doc.exists():
            ar_doc.unlink()


def make_translation(original_text: str, lang: str = "xx", dir_: str = "rtl") -> str:
    """A translation of the Acme 'Decision log.md' text: front matter with lang, dir, translation_of 'Decision log.md' and source_hash = pc.body_hash(original_text); checks and source_hashes dropped; every word in WORDS replaced; ids, dates and numbers untouched."""
    fm, body = pc.split_front_matter(original_text)
    if fm is None:
        fm = {}
    fm.pop("checks", None)
    fm.pop("source_hashes", None)
    fm["lang"] = lang
    fm["dir"] = dir_
    fm["translation_of"] = "Decision log.md"
    fm["source_hash"] = pc.body_hash(original_text)

    for eng, trans in sorted(WORDS.items(), key=lambda x: -len(x[0])):
        body = body.replace(eng, trans)

    import yaml
    fm_yaml = yaml.safe_dump(fm, sort_keys=False)
    return f"---\n{fm_yaml}---\n{body}"
