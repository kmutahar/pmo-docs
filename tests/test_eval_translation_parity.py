"""Checks the translation-parity eval fixture without running the eval. Run from the repo root: python3 -m unittest tests.test_eval_translation_parity"""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402

SCAFFOLD = REPO / "evals/translation-parity/scaffold.sh"
PARITY = REPO / "skills/pmo-docs/scripts/parity_check.py"


class TranslationParityEval(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp))
        subprocess.run(["bash", str(SCAFFOLD)], cwd=self.tmp, check=True)
        self.docs = self.tmp / "pmo/documents"

    def test_source_hash_matches_the_original(self):
        orig = (self.docs / "Decision log.md").read_text(encoding="utf-8")
        trans = (self.docs / "Decision log.xx.md").read_text(encoding="utf-8")
        fm, _ = pc.split_front_matter(trans)
        self.assertEqual(fm["source_hash"], pc.body_hash(orig),
                         "Acme's decision log changed: update source_hash in evals/translation-parity/scaffold.sh")
        self.assertEqual(pc.split_front_matter(orig)[0]["status"], "finished")

    def test_parity_reports_the_two_faults(self):
        p = subprocess.run([sys.executable, str(PARITY), "--project", str(self.tmp)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertRegex(p.stdout, r"`Summary` table 1: rows count differs")
        self.assertRegex(p.stdout, r"DEC-1 - Use weekly releases`: numbers differ")


if __name__ == "__main__":
    unittest.main()
