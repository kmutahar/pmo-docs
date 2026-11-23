"""Tests for the priorities -> goals rename: the register in a fresh project, and migrate/0002_goals_register.py on a v0.1.0-style project. Run from the repo root: python3 -m unittest tests.test_goals_register"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
FIXTURE = REPO / "tests/fixtures/acme-0.1"  # schema_version 1, unpadded ids, a priorities register with P- ids
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import docs_audit  # noqa: E402
import pmo_common as pc  # noqa: E402

DOC = """---
title: Notes
type: x
status: draft
---

# Notes

Goal `P-2` waits for P-1; UTF-8 and XP-1 stay.

```
P-1 inside a fence stays
```
"""


def run(script, root, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), "--project", str(root), *args],
                       capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout + p.stderr


def snapshot(root):
    return {p: p.read_bytes() for p in Path(root).rglob("*") if p.is_file()}


class Defaults(unittest.TestCase):
    def test_register_is_goals_with_prefix_gl(self):
        reg = pc.load_config(REPO / "examples/acme")["registers"]
        self.assertNotIn("priorities", reg)
        self.assertEqual((reg["goals"]["file"], reg["goals"]["view"], reg["goals"]["prefix"]), ("goals.yaml", "goals.md", "GL"))
        self.assertIn("objectives", reg["goals"]["fields"])
        self.assertNotIn("goals", reg["goals"]["fields"])
        self.assertEqual(reg["goals"]["refs"], {"depends_on": "goals", "blocks": "goals"})


class Migrate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "p"
        shutil.copytree(FIXTURE, self.root)
        (self.root / "pmo/views").mkdir(exist_ok=True)
        (self.root / "pmo/views/priorities.md").write_text("# Priorities\n\n| P-1 |\n", encoding="utf-8")
        (self.root / "pmo/documents").mkdir(exist_ok=True)
        (self.root / "pmo/documents/Notes.md").write_text(DOC, encoding="utf-8")
        self.reg = self.root / "pmo/registers"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def migrate(self, name="0002_goals_register.py", *args):
        return run(f"migrate/{name}", self.root, *args)

    def test_renames_file_field_ids_and_views(self):
        code, out = self.migrate()
        self.assertEqual(code, 0, out)
        self.assertFalse((self.reg / "priorities.yaml").exists())
        self.assertFalse((self.root / "pmo/views/priorities.md").exists())
        text = (self.reg / "goals.yaml").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("goals:\n"), text)
        self.assertIn("{id: GL-1, title: Launch portal beta, objectives: [O-1]", text)
        self.assertIn("depends_on: [GL-1]", text)
        self.assertNotIn("goals: [", text)
        self.assertIn("# Goals", (self.root / "pmo/views/goals.md").read_text(encoding="utf-8"))
        doc = (self.root / "pmo/documents/Notes.md").read_text(encoding="utf-8")
        self.assertIn("Goal `GL-2` waits for GL-1; UTF-8 and XP-1 stay.", doc)
        self.assertIn("P-1 inside a fence stays", doc)
        self.assertEqual(run("render_views.py", self.root, "--check")[0], 0)

    def test_after_the_padding_migration_ids_are_padded(self):
        self.assertEqual(self.migrate("0001_pad_ids.py", "--yes")[0], 0)
        self.assertTrue((self.reg / "priorities.yaml").exists())  # the padding leaves a register the skill no longer knows
        code, out = self.migrate()
        self.assertEqual(code, 0, out)
        self.assertIn("{id: GL-001,", (self.reg / "goals.yaml").read_text(encoding="utf-8"))
        self.assertIn("depends_on: [GL-001]", (self.reg / "goals.yaml").read_text(encoding="utf-8"))
        self.assertIn("Goal `GL-002` waits for GL-001", (self.root / "pmo/documents/Notes.md").read_text(encoding="utf-8"))
        self.assertEqual(run("render_views.py", self.root, "--check")[0], 0)

    def test_before_the_padding_migration_the_padding_finishes_the_job(self):
        self.assertEqual(self.migrate()[0], 0)
        self.assertEqual(self.migrate("0001_pad_ids.py", "--yes")[0], 0)
        self.assertIn("{id: GL-001,", (self.reg / "goals.yaml").read_text(encoding="utf-8"))
        self.assertEqual(run("render_views.py", self.root, "--check")[0], 0)

    def test_second_run_changes_nothing(self):
        self.assertEqual(self.migrate()[0], 0)
        before = snapshot(self.root)
        code, out = self.migrate()
        self.assertEqual(code, 0, out)
        self.assertEqual(before, snapshot(self.root))

    def test_both_files_present_is_refused(self):
        (self.reg / "goals.yaml").write_text("goals: []\n", encoding="utf-8")
        before = snapshot(self.root)
        code, out = self.migrate()
        self.assertEqual(code, 2)
        self.assertIn("both exist", out)
        self.assertEqual(before, snapshot(self.root))

    def test_config_names_and_the_field_in_an_override(self):
        cfg = self.root / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8") + "registers:\n  priorities:\n    fields: [id, title, goals, output, depends_on, blocks, owner, acceptance, accepted_by, accepted_on, status, note, due]\n"
                       "  tasks:\n    refs: {tests: tests, extra: priorities}\n"
                       "doc_types:\n  project-plan:\n    generated_from: [tasks, priorities, teams]\n    regenerate: when priorities change\n",
                       encoding="utf-8")
        code, out = self.migrate()
        self.assertEqual(code, 0, out)
        new = cfg.read_text(encoding="utf-8")
        self.assertIn("  goals:\n    fields: [id, title, objectives, output, depends_on, blocks, owner, acceptance, accepted_by, accepted_on, status, note, due]\n", new)
        self.assertIn("extra: goals}", new)
        self.assertIn("generated_from: [tasks, goals, teams]", new)
        self.assertIn("regenerate: when priorities change", new)  # running text is not a name
        self.assertNotIn("priorities:", new)

    def test_current_document_stays_current(self):
        old = hashlib.sha256((self.reg / "priorities.yaml").read_bytes()).hexdigest()[:8]
        doc = self.root / "pmo/documents/Plan.md"
        doc.write_text(f'---\ntitle: Plan\ntype: project-plan\nstatus: finished\nsource_hashes: {{priorities: "{old}"}}\n---\n\n# Plan\n', encoding="utf-8")
        self.assertEqual(self.migrate()[0], 0)
        new = docs_audit.register_hash(self.root, pc.load_config(self.root), "goals")
        self.assertNotEqual(old, new)
        self.assertIn(f'source_hashes: {{goals: "{new}"}}', doc.read_text(encoding="utf-8"))

    def test_names_file_follows(self):
        (self.root / "pmo/names.ar.yaml").write_text("approved:\n  priorities:\n    P-1:\n      goals: x\n      title: y\n", encoding="utf-8")
        cfg = self.root / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8") + "languages:\n  translations: [ar]\n  ar: {label: AR, dir: rtl, names: pmo/names.ar.yaml}\n", encoding="utf-8")
        code, out = self.migrate()
        self.assertEqual(code, 0, out)
        self.assertEqual((self.root / "pmo/names.ar.yaml").read_text(encoding="utf-8"), "approved:\n  goals:\n    GL-1:\n      objectives: x\n      title: y\n")


if __name__ == "__main__":
    unittest.main()
