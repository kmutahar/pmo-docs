"""Tests dev/scrub-coverage.py on a fake source folder (counts only). Run from the repo root: python3 -m unittest tests.test_scrub_coverage"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "dev/scrub-coverage.py"


class ScrubCoverage(unittest.TestCase):
    def test_counts_caught_and_uncaught_names(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            src = tmp / "src"
            (src / "data").mkdir(parents=True)
            (src / "registers").mkdir()
            (src / "data/roster.md").write_text(
                "| slug | role | x | name en | name ar |\n|---|---|---|---|---|\n| jdoe | dev | - | Jane Doe | جين |\n", encoding="utf-8")
            (src / "config.yaml").write_text("project:\n  name: Zeta Works\nsubprojects:\n  alpha: {}\n", encoding="utf-8")
            (src / "registers/tasks.yaml").write_text("tasks:\n  - owner: jdoe\n    assignee: Bob\n", encoding="utf-8")
            names = tmp / "names"
            names.write_text("jane\n\\bjdoe\\b\n", encoding="utf-8")
            out = tmp / "out.txt"
            p = subprocess.run([sys.executable, str(SCRIPT), str(src), str(names), str(out)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("roster slug: 1 found, 0 not caught", p.stdout)
            self.assertIn("name part en: 2 found, 1 not caught", p.stdout)  # Doe is not caught, Jane is
            self.assertIn("config.project values: 1 found, 1 not caught", p.stdout)
            self.assertIn("register people values: 2 found, 1 not caught", p.stdout)  # Bob
            rows = out.read_text(encoding="utf-8").splitlines()
            self.assertIn("name part en\tDoe", rows)
            self.assertNotIn("roster slug\tjdoe", rows)

    def test_help(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0)
        self.assertIn("NAMES_FILE", p.stdout)


if __name__ == "__main__":
    unittest.main()
