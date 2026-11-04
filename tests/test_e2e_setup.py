"""End-to-end: setup.py on an empty temp folder, then every checker passes. Run from the repo root: python3 -m unittest tests.test_e2e_setup"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"


def tool(name, project, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / name), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


class EndToEnd(unittest.TestCase):
    def test_setup_then_all_checks_pass(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        code, out = tool("setup.py", root, "--name", "Demo", "--manager", "Pat Example")
        self.assertEqual(code, 0, out)
        for name, args in [("render_views.py", ["--check"]), ("structure_check.py", []), ("docs_audit.py", [])]:
            code, out = tool(name, root, *args)
            self.assertEqual(code, 0, f"{name}: {out}")


if __name__ == "__main__":
    unittest.main()
