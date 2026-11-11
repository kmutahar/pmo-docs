"""Tests for draft-technical playbook. Run from the repo root: python3 -m unittest discover tests"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/pmo-docs/scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import pmo_common as pc  # noqa: E402
from test_stacks import HEADINGS  # noqa: E402

DOC_TYPES = (
    "entity-lifecycle",
    "api-reference",
    "integration-guide",
    "architecture-overview",
    "user-guide",
)


class DraftTechnical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = pc.SKILL / "references" / "draft-technical.md"
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.lines = cls.text.splitlines()

    def test_front_matter_then_reads(self):
        self.assertTrue(self.path.exists())
        self.assertTrue(20 <= len(self.lines) < 80, f"line count {len(self.lines)} not in 20..80")
        fm, body = pc.split_front_matter(self.text, strict=True)
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("playbook_version"), 1)
        self.assertIsInstance(fm["playbook_version"], int)
        self.assertTrue(body.lstrip().startswith("Reads:"), "Body must start with Reads:")
        self.assertIn("## Steps", body)
        self.assertIn("## Do not", body)

    def test_names_all_five_doc_types(self):
        for dt in DOC_TYPES:
            self.assertIn(dt, self.text)

    def test_every_path_it_names_exists(self):
        refs = re.findall(r"references/[a-zA-Z0-9_\-\./]+", self.text)
        self.assertGreater(len(refs), 0)
        for ref in refs:
            ref_clean = ref.rstrip("`'\".,;:)")
            ref_path = pc.SKILL / ref_clean
            self.assertTrue(ref_path.exists(), f"Referenced path does not exist: {ref_clean}")

    def test_names_no_tool(self):
        forbidden_tools = ["graphify", "trail", "ctags", "sourcegraph", "lsif"]
        for tool in forbidden_tools:
            self.assertNotIn(tool, self.text.lower())
        self.assertIn("code-graph or index tool", self.text)

    def test_lists_the_six_stack_headings(self):
        for heading in HEADINGS:
            self.assertIn(heading, self.text)


if __name__ == "__main__":
    unittest.main()
