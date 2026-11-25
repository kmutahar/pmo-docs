"""Tests for scripts/finish.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_finish"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "skills/pmo-docs/scripts/finish.py"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def run(project, *args):
    p = subprocess.run([sys.executable, str(TOOL), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class Finish(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        src = next(p for p in sorted((self.root / "pmo/documents").glob("*.md")) if "status: finished" in p.read_text(encoding="utf-8"))
        self.doc = src.with_name("Draft under test.md")
        shutil.copyfile(src, self.doc)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def draft(self, text):
        t = self.doc.read_text(encoding="utf-8")
        self.doc.write_text(text(t), encoding="utf-8")

    def test_strips_comments_and_checks_and_sets_status(self):
        self.draft(lambda t: re.sub(r"^status: finished", "status: draft\nchecks:\n  - kind: required_cells\n    section: X\n    columns: [A]", t, count=1, flags=re.M)
                   .replace("\n# ", "\n<!-- note -->\n# ", 1) + "\n```\n<!-- keep -->\n```\n")
        code, out, err = run(self.root, "--as-of", "2026-05-06", str(self.doc))
        self.assertEqual(code, 0, out + err)
        t = self.doc.read_text(encoding="utf-8")
        self.assertIn("status: finished", t)
        self.assertRegex(t, r"last_updated: \"?2026-05-06")
        self.assertNotIn("checks:", t)
        self.assertNotIn("<!-- note -->", t)
        self.assertIn("<!-- keep -->", t)

    def test_errors_leave_the_file_unchanged(self):
        self.draft(lambda t: t.replace("status: finished", "status: draft", 1) + "\nleft {{placeholder}} here\n")
        before = self.doc.read_text(encoding="utf-8")
        code, out, err = run(self.root, str(self.doc))
        self.assertEqual(code, 1)
        self.assertIn("placeholder", out)
        self.assertEqual(self.doc.read_text(encoding="utf-8"), before)

    def test_a_finished_document_is_refused(self):
        code, out, err = run(self.root, str(self.doc))
        self.assertEqual(code, 1)
        self.assertIn("not a draft", out)

    def test_a_file_outside_the_project_is_refused(self):
        outside = self.root.parent / "x.md"
        outside.write_text("---\nstatus: draft\n---\n", encoding="utf-8")
        code, out, err = run(self.root, str(outside))
        self.assertEqual(code, 2)

    def test_a_file_inside_dot_git_is_refused(self):
        git_doc = self.root / ".git/x.md"
        git_doc.parent.mkdir(parents=True)
        shutil.copyfile(self.doc, git_doc)
        code, _, err = run(self.root, str(git_doc))
        self.assertEqual(code, 2)
        self.assertIn(".git", err)
        link = self.root / "pmo/documents/Link.md"
        link.symlink_to(git_doc)
        code, _, err = run(self.root, str(link))
        self.assertEqual(code, 2)
        self.assertIn(".git", err)


if __name__ == "__main__":
    unittest.main()
