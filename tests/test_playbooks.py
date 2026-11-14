"""Tests for playbooks and playbook overrides. Run from the repo root: python3 -m unittest discover tests"""
import re
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
        (root / "pmo").mkdir(parents=True)
        (root / "pmo/config.yaml").write_text("schema_version: 1\n", encoding="utf-8")
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

    def test_do_not_lists_point_to_skill_md(self):
        for name in ("intake", "draft", "govern", "plan", "track", "translate", "docs-audit"):
            with self.subTest(name):
                text = (pc.SKILL / "references" / f"{name}.md").read_text(encoding="utf-8")
                _, after = text.split("## Do not", 1)
                self.assertIn("Break a rule in `SKILL.md`", after)

    def test_extend_and_schedule_cite_rule_3(self):
        for name in ("extend", "schedule"):
            with self.subTest(name):
                text = (pc.SKILL / "references" / f"{name}.md").read_text(encoding="utf-8")
                self.assertIn("a change to the config, a template or a playbook is always shown first", text)

    def test_govern_trigger_covers_both_cases(self):
        text = (pc.SKILL / "references/govern.md").read_text(encoding="utf-8")
        self.assertIn("say it needs a change request and ask before recording one", text)

    def test_weekly_status_runs_the_generator_first(self):
        text = (pc.SKILL / "references/weekly-status.md").read_text(encoding="utf-8")
        self.assertIn("generate.py status-report", text)
        self.assertIn("Count only tasks whose", text)
        self.assertLess(text.index("generate.py status-report"), text.index("Count only tasks whose"))
        self.assertIn("do not recount them by hand", text)

    def test_monthly_status_follows_weekly_steps(self):
        text = (pc.SKILL / "references/monthly-status.md").read_text(encoding="utf-8")
        self.assertIn("steps 2 and 4", text)

    def test_draft_technical_lists_shipped_stacks(self):
        stacks = sorted(p.stem for p in (pc.SKILL / "references/stacks").glob("*.md"))
        self.assertGreater(len(stacks), 0)
        text = (pc.SKILL / "references/draft-technical.md").read_text(encoding="utf-8")
        for stack in stacks:
            with self.subTest(stack):
                self.assertIn(stack, text)


class PlaybookWording(unittest.TestCase):
    def test_gitignore_is_documented(self):
        skill = (pc.SKILL / "SKILL.md").read_text(encoding="utf-8")
        editor_line = next(line for line in skill.splitlines() if line.startswith("- **Editor.**"))
        self.assertIn("pmo/.gitignore", editor_line)
        self.assertIn("except `pmo/.me`", (pc.SKILL / "references/git.md").read_text(encoding="utf-8"))
        self.assertIn(".gitignore", (pc.SKILL / "references/setup.md").read_text(encoding="utf-8"))

    def test_no_padded_id_examples(self):
        pat = re.compile(r"\b(?:T|R|I|A|D|DEC|ACT|CR|MTG|M|P|O|B|TM|REQ|TST|ENV|PERM)-0[0-9]+\b")
        files = [pc.SKILL / "SKILL.md", *(pc.SKILL / "references").rglob("*.md")]
        for f in files:
            with self.subTest(f.relative_to(pc.SKILL)):
                for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    self.assertIsNone(pat.search(line), f"{f.name}:{lineno}: {line}")

    def test_git_md_holds_the_workflow(self):
        text = (pc.SKILL / "references/git.md").read_text(encoding="utf-8")
        self.assertIn("name: pmo check", text)
        self.assertIn("<version>", text)
        self.assertNotIn("The README has the full file", text)

    def test_finish_steps_and_publish_title(self):
        publish = (pc.SKILL / "references/publish.md").read_text(encoding="utf-8")
        self.assertNotIn("# Recipe: publish", publish)
        finish = (pc.SKILL / "references/finish.md").read_text(encoding="utf-8")
        self.assertFalse(any(line.startswith("5. **Translations**") for line in finish.splitlines()))

    def test_conventions_front_matter_rows(self):
        text = (pc.SKILL / "references/conventions.md").read_text(encoding="utf-8")
        self.assertIn("| `editor` |", text)
        self.assertIn("| `covers_from`, `covers_to` |", text)

    def test_extend_md_explains_another_draft_language(self):
        text = (pc.SKILL / "references/extend.md").read_text(encoding="utf-8")
        self.assertIn("Draft in another language", text)
        self.assertIn("generator: null", text)


if __name__ == "__main__":
    unittest.main()
