"""Tests for scripts/where.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_where"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "skills/pmo-docs/scripts/where.py"


def run(project, *args):
    p = subprocess.run([sys.executable, str(TOOL), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def fields(out):
    return dict(line.split(": ", 1) for line in out.splitlines() if ": " in line)


class Where(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_document_with_period(self):
        code, out, _ = run(self.root, "status-report", "2026-03")
        f = fields(out)
        self.assertEqual(code, 0)
        self.assertEqual(f["type"], "status-report")
        self.assertEqual(f["document"], "pmo/documents/2026-03 - Status report.md")
        self.assertEqual(f["document_exists"], "yes")
        self.assertIn("tasks", f["generated_from"].split(", "))
        self.assertEqual(f["stale_days"], "30")

    def test_document_without_period_in_name(self):
        f = fields(run(self.root, "decision-log")[1])
        self.assertEqual(f["document"], "pmo/documents/Decision log.md")
        self.assertEqual(f["document_exists"], "yes")

    def test_missing_document(self):
        f = fields(run(self.root, "status-report", "2030-01")[1])
        self.assertEqual(f["document_exists"], "no")

    def test_period_defaults_to_current_month(self):
        f = fields(run(self.root, "status-report", "--as-of", "2026-03-15")[1])
        self.assertEqual(f["document"], "pmo/documents/2026-03 - Status report.md")

    def test_week_option(self):
        f = fields(run(self.root, "status-report", "--week", "--as-of", "2026-03-15")[1])
        self.assertEqual(f["document"], "pmo/documents/2026-W11 - Status report.md")

    def test_skill_template_when_no_override(self):
        f = fields(run(self.root, "status-report", "2026-03")[1])
        self.assertEqual(f["template_source"], "skill")
        self.assertTrue(f["template"].endswith("assets/templates/status-report.md"))

    def test_project_template_wins(self):
        tpl = self.root / "pmo/templates/status-report.md"
        tpl.parent.mkdir(parents=True)
        tpl.write_text("---\ntype: status-report\ntemplate_version: 3\nbased_on: status-report@2\n---\n# x\n", encoding="utf-8")
        f = fields(run(self.root, "status-report", "2026-03")[1])
        self.assertEqual(f["template_source"], "project")
        self.assertEqual(f["template"], "pmo/templates/status-report.md")
        self.assertEqual(f["template_exists"], "yes")
        self.assertEqual(f["template_version"], "3")
        self.assertEqual(f["based_on"], "status-report@2")

    def test_unknown_type_exits_2_and_lists_types(self):
        code, _, err = run(self.root, "no-such-type")
        self.assertEqual(code, 2)
        self.assertIn("status-report", err)

    def test_help(self):
        self.assertEqual(run(self.root, "--help")[0], 0)

    def test_missing_project_exits_2(self):
        self.assertEqual(run(self.root / "nope", "decision-log")[0], 2)


if __name__ == "__main__":
    unittest.main()
