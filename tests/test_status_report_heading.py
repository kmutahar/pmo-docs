"""Tests for migrate/0003_status_report_heading.py and the generator's message for the old heading. Run from the repo root: python3 -m unittest tests.test_status_report_heading"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
OLD = "## Risks and issues"
NEW = "## Risks and issues: changes since last report"


def run(script, root, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), "--project", str(root), *args],
                       capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout + p.stderr


class Heading(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.tpl = self.root / "pmo/templates"
        self.tpl.mkdir(parents=True, exist_ok=True)
        default = (REPO / "skills/pmo-docs/assets/templates/status-report.md").read_text(encoding="utf-8")
        self.old = default.replace(NEW, OLD)
        self.assertNotEqual(self.old, default)
        (self.tpl / "status-report.md").write_text(self.old, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def read(self, name):
        return (self.tpl / name).read_text(encoding="utf-8")

    def test_renames_the_heading_and_says_so(self):
        code, out = run("migrate/0003_status_report_heading.py", self.root)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read("status-report.md"), self.old.replace(OLD, NEW))
        self.assertEqual(out.count("\n"), 1, out)
        self.assertIn("pmo/templates/status-report.md", out)

    def test_second_run_changes_nothing_and_prints_nothing(self):
        run("migrate/0003_status_report_heading.py", self.root)
        before = self.read("status-report.md")
        code, out = run("migrate/0003_status_report_heading.py", self.root)
        self.assertEqual((code, out), (0, ""))
        self.assertEqual(self.read("status-report.md"), before)

    def test_new_heading_present_is_left_alone(self):
        text = self.old + f"\n{NEW}\n"
        (self.tpl / "status-report.md").write_text(text, encoding="utf-8")
        self.assertEqual(run("migrate/0003_status_report_heading.py", self.root), (0, ""))
        self.assertEqual(self.read("status-report.md"), text)

    def test_copies_change_but_translations_and_other_templates_do_not(self):
        (self.tpl / "status-report-weekly.md").write_text(self.old, encoding="utf-8")
        (self.tpl / "status-report.ar.md").write_text(self.old, encoding="utf-8")
        (self.tpl / "risk-note.md").write_text(f"---\ntype: risk-note\n---\n\n{OLD}\n", encoding="utf-8")
        code, out = run("migrate/0003_status_report_heading.py", self.root)
        self.assertEqual(code, 0, out)
        self.assertIn(NEW, self.read("status-report-weekly.md"))
        self.assertEqual(self.read("status-report.ar.md"), self.old)
        self.assertEqual(self.read("risk-note.md"), f"---\ntype: risk-note\n---\n\n{OLD}\n")

    def test_only_the_exact_heading_line_changes(self):
        text = f"---\ntype: status-report\n---\n\n{OLD}\n\n{OLD} (older)\n"
        (self.tpl / "status-report.md").write_text(text, encoding="utf-8")
        run("migrate/0003_status_report_heading.py", self.root)
        self.assertEqual(self.read("status-report.md"), f"---\ntype: status-report\n---\n\n{NEW}\n\n{OLD} (older)\n")

    def test_generator_names_the_new_heading(self):
        code, out = run("generate.py", self.root, "status-report", "2026-03", "--stdout")
        self.assertEqual(code, 2, out)
        self.assertIn(f"rename it to `{NEW}`", out)
        run("migrate/0003_status_report_heading.py", self.root)
        self.assertEqual(run("generate.py", self.root, "status-report", "2026-03", "--stdout")[0], 0)


if __name__ == "__main__":
    unittest.main()
