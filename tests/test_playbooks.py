"""Tests for playbooks and playbook overrides. Run from the repo root: python3 -m unittest discover tests"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


class PlaybookFrontMatter(unittest.TestCase):
    def test_every_reference_file_has_playbook_version_and_reads(self):
        ref_dir = pc.SKILL / "references"
        files = list(ref_dir.rglob("*.md"))
        self.assertGreater(len(files), 0)
        for f in files:
            with self.subTest(f.name):
                fm, body = pc.split_front_matter(f.read_text(encoding="utf-8"), strict=True)
                self.assertIsNotNone(fm, f"{f} has no front matter")
                self.assertIn("playbook_version", fm)
                self.assertIsInstance(fm["playbook_version"], int)
                if f.parent.name == "stacks":
                    self.assertTrue(body.lstrip().startswith("Detected by:"), f"{f} body does not start with Detected by:")
                else:
                    self.assertTrue(body.lstrip().startswith("Reads:"), f"{f} body does not start with Reads:")

    def test_find_asset_playbooks(self):
        tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp_dir)
        root = tmp_dir / "project"
        root.mkdir()
        cfg = pc.load_config(root)

        # Default returns skill file
        path, src = pc.find_asset(root, cfg, "playbooks", "draft.md")
        self.assertEqual(src, "skill")
        self.assertEqual(path, pc.SKILL / "references/draft.md")

        # Project file wins when present
        pb = root / "pmo/playbooks/draft.md"
        pb.parent.mkdir(parents=True, exist_ok=True)
        pb.write_text("---\nplaybook_version: 1\n---\nReads: ...\n", encoding="utf-8")
        path, src = pc.find_asset(root, cfg, "playbooks", "draft.md")
        self.assertEqual(src, "project")
        self.assertEqual(path, pb)

        # Subfolder works (e.g. stacks/x.md)
        path, src = pc.find_asset(root, cfg, "playbooks", "stacks/x.md")
        self.assertEqual(src, "skill")
        self.assertEqual(path, pc.SKILL / "references/stacks/x.md")

        stack_file = root / "pmo/playbooks/stacks/x.md"
        stack_file.parent.mkdir(parents=True, exist_ok=True)
        stack_file.write_text("---\nplaybook_version: 1\n---\nReads: ...\n", encoding="utf-8")
        path, src = pc.find_asset(root, cfg, "playbooks", "stacks/x.md")
        self.assertEqual(src, "project")
        self.assertEqual(path, stack_file)

        # ../x.md raises ValueError
        with self.assertRaises(ValueError):
            pc.find_asset(root, cfg, "playbooks", "../x.md")


if __name__ == "__main__":
    unittest.main()
