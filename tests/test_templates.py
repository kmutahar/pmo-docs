"""Tests for the default templates in skills/pmo-docs/assets/templates. Run from the repo root: python3 -m unittest tests.test_templates"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
import pmo_common as pc  # noqa: E402
import structure_check as sc  # noqa: E402

TEMPLATES = REPO / "skills/pmo-docs/assets/templates"
CFG = pc.load_config(".", must_exist=False)
REQUIRED = {"title", "type", "project", "manager", "template_version", "status", "last_updated"}
FORBIDDEN = {"owner", "scope", "lang", "dir"}  # fix 20: manager, not owner; English only in v0.1
KINDS = {
    "required_cells": ("section", "columns"),
    "equal_count": ("rows_in", "headings_in", "level"),
    "listed_have_sections": ("listed_in", "sections_in", "level"),
}
NAME_KEYS = ("section", "rows_in", "headings_in", "listed_in", "sections_in")


def present():
    return [(t, TEMPLATES / info["template"]) for t, info in CFG["doc_types"].items() if (TEMPLATES / info["template"]).exists()]


class Templates(unittest.TestCase):
    def test_all_doc_types_have_a_template(self):
        missing = [t for t, info in CFG["doc_types"].items() if not (TEMPLATES / info["template"]).exists()]
        self.assertEqual(missing, [])

    def test_no_stray_template_files(self):
        wanted = {info["template"] for info in CFG["doc_types"].values()}
        self.assertEqual({p.name for p in TEMPLATES.glob("*") if p.is_file()} - wanted, set())

    def test_front_matter(self):
        for t, f in present():
            with self.subTest(t):
                fm, _ = pc.split_front_matter(f.read_text(encoding="utf-8"), strict=True)
                self.assertGreaterEqual(set(fm), REQUIRED)
                self.assertEqual(set(fm) & FORBIDDEN, set())
                self.assertEqual(fm["type"], t)
                self.assertIsInstance(fm["template_version"], int)
                self.assertEqual(fm["status"], "draft")
                self.assertEqual(fm["project"], "{{project}}")
                self.assertEqual(fm["manager"], "{{manager}}")

    def test_checks_are_valid_and_name_real_sections(self):
        for t, f in present():
            with self.subTest(t):
                fm, body = pc.split_front_matter(f.read_text(encoding="utf-8"), strict=True)
                titles = {sc.norm(h) for _, h, _ in sc.sections(body)}
                for c in fm.get("checks") or []:
                    self.assertIn(c["kind"], KINDS)
                    for key in KINDS[c["kind"]]:
                        self.assertIn(key, c, c)
                    for key in NAME_KEYS:
                        if key in c:
                            self.assertIn(sc.norm(c[key]), titles, f"{t}: no heading {c[key]!r}")

    def test_reads_comment_matches_generated_from(self):
        # fix 5: the first HTML comment is `<!-- Reads: tasks, risks -->` and lists every register the template uses
        for t, f in present():
            with self.subTest(t):
                m = re.search(r"<!--\s*Reads:\s*(.*?)\s*-->", f.read_text(encoding="utf-8"))
                self.assertIsNotNone(m, "missing <!-- Reads: ... --> comment")
                reads = [r.strip() for r in m.group(1).split(",") if r.strip()]
                self.assertEqual(sorted(reads), sorted(CFG["doc_types"][t]["generated_from"]))
                self.assertTrue(set(reads) <= set(CFG["registers"]))

    def test_only_known_placeholders_and_no_leftovers(self):
        for t, f in present():
            with self.subTest(t):
                text = f.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"\{\{\s*(subproject|owner)\s*\}\}")
                self.assertNotRegex(text, r"[؀-ۿ]")  # no Arabic in v0.1
                self.assertNotRegex(text, r"https?://")

    def test_acme_documents_pass_structure_check(self):
        root = Path(tempfile.mkdtemp()) / "acme"
        try:
            shutil.copytree(REPO / "examples/acme", root)
            p = subprocess.run([sys.executable, str(SCRIPTS / "structure_check.py"), "--project", str(root)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        finally:
            shutil.rmtree(root.parent)

    def test_no_template_line_is_a_bare_bullet(self):
        for f in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(f.name):
                for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    self.assertNotRegex(line, r"^-\s*$", f"{f.name}:{lineno}")

    def test_open_questions_bullet_is_a_placeholder(self):
        for f in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(f.name):
                _, body = pc.split_front_matter(f.read_text(encoding="utf-8"), strict=True)
                oq = [txt for _, title, txt in sc.sections(body) if title == "Open questions"]
                if oq:
                    bullets = [ln.strip() for ln in oq[0].splitlines() if ln.lstrip().startswith("- ")]
                    self.assertTrue(bullets, f"{f.name}: no bullet under Open questions")
                    self.assertEqual(bullets[0], "- {{question}}")


if __name__ == "__main__":
    unittest.main()
