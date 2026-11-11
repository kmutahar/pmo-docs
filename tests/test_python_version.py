"""Every script stops with a clear message on Python below 3.10. Run from the repo root: python3 -m unittest tests.test_python_version"""
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"
# Pretend to be Python 3.9 after the stdlib is loaded, then run the script as __main__.
FAKE = "import runpy, sys; sys.version_info = (3, 9, 0, 'final', 0); runpy.run_path(sys.argv[1], run_name='__main__')"


class PythonVersion(unittest.TestCase):
    def test_every_script_stops_below_3_10(self):
        for name in ("setup", "where", "generate", "render_views", "structure_check", "parity_check", "docs_audit", "overdue", "publish", "pmo_common"):
            with self.subTest(script=name):
                p = subprocess.run([sys.executable, "-c", FAKE, str(SCRIPTS / f"{name}.py"), "--help"], capture_output=True, text=True, encoding="utf-8")
                self.assertNotEqual(p.returncode, 0)
                self.assertIn("needs Python 3.10 or newer (this is 3.9)", p.stderr)


if __name__ == "__main__":
    unittest.main()
