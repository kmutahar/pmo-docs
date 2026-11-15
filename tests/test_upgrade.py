"""A project made with v0.1.0 (frozen in tests/fixtures/acme-0.1) still renders, checks and audits clean. Run from the repo root: python3 -m unittest tests.test_upgrade"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
FIXTURE = REPO / "tests/fixtures/acme-0.1"  # v0.1.0 config and registers; never edit again, a later format change adds its own fixture beside it
# One edit, 2026-11: `origin` values (kickoff, review, test) became `stated`, because 0.7.3 limited `origin` to stated/proposed.


def run(script, project, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), "--project", str(project), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


class UpgradeFromV01(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(FIXTURE, self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_render_check_and_audit(self):
        code, out = run("render_views.py", self.root)
        self.assertEqual(code, 0, out)
        code, out = run("render_views.py", self.root, "--check")
        self.assertEqual(code, 0, out)
        code, out = run("docs_audit.py", self.root)  # the fixture has no documents, so nothing can be stale
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
