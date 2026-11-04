"""Tests for scripts/render_views.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_render_views"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "skills/pmo-docs/scripts/render_views.py"


def run(project, *args):
    p = subprocess.run([sys.executable, str(TOOL), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


class RenderViews(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        self.views = self.root / "pmo/views"
        for v in self.views.glob("*.md"):  # start with no views; the committed ones are tested below
            v.unlink()

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def append(self, name, line):
        with open(self.reg / f"{name}.yaml", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def test_acme_is_valid_and_renders(self):
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        text = (self.views / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("GENERATED", text)
        self.assertLess(text.index("| high |"), text.index("| medium |"))  # priority_order from config
        self.assertLess(text.index("| medium |"), text.index("| low |"))
        self.assertTrue((self.views / "risks.md").exists())

    def test_origin_is_accepted_on_every_register(self):
        entries = {
            "tasks": "{id: T-90, title: x, status: not-started, origin: proposed}",
            "actions": "{id: ACT-90, text: x, status: open, origin: proposed}",
            "decisions": "{id: DEC-90, title: x, status: proposed, origin: proposed}",
            "changes": "{id: CR-90, title: x, status: proposed, origin: proposed}",
            "meetings": "{id: MTG-90, title: x, origin: proposed}",
            "milestones": "{id: M-90, title: x, status: not-started, origin: proposed}",
            "dependencies": "{id: D-90, text: x, origin: proposed}",
            "teams": "{id: TM-90, heading: x, origin: proposed}",
            "priorities": "{id: P-90, title: x, status: not-started, origin: proposed}",
        }
        for name, line in entries.items():
            self.append(name, "  - " + line)
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

    def test_missing_register_is_not_an_error(self):
        (self.reg / "teams.yaml").unlink()
        (self.reg / "priorities.yaml").unlink()
        self.assertEqual(run(self.root)[0], 0)
        self.assertFalse((self.views / "teams.md").exists())

    def test_bad_enum_date_and_unknown_field(self):
        self.append("tasks", "  - {id: T-9, title: x, status: finished, due: TBD, colour: red}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        for part in ("status 'finished'", "due 'TBD'", "unexpected field 'colour'"):
            self.assertIn(part, out)
        self.assertFalse((self.views / "tasks.md").exists())  # nothing written on errors

    def test_impossible_date_is_reported(self):
        self.append("tasks", "  - {id: T-9, title: x, status: done, due: 2026-02-30}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("tasks.yaml: not readable", out)

    def test_priority_and_owner_checks(self):
        self.append("risks", "  - {id: R-9, title: x, probability: huge, owner: zed, status: open}")
        out = run(self.root)[1]
        self.assertIn("probability 'huge'", out)
        self.assertIn("owner 'zed' is not in the roster", out)

    def test_duplicate_id_across_registers(self):
        self.append("actions", "  - {id: T-1, text: x, status: open}")
        self.assertIn("duplicate id T-1", run(self.root)[1])

    def test_multi_line_entry_fails(self):
        self.append("tasks", "  - {id: T-9, title: x,\n      status: done}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("one line", out)

    def test_deterministic(self):
        run(self.root)
        first = {p.name: p.read_bytes() for p in self.views.glob("*.md")}
        run(self.root)
        self.assertEqual(first, {p.name: p.read_bytes() for p in self.views.glob("*.md")})

    def test_check_detects_stale_and_writes_nothing(self):
        code, out = run(self.root, "--check")
        self.assertEqual(code, 1)  # no views yet
        self.assertIn("stale view", out)
        self.assertFalse((self.views / "tasks.md").exists())
        run(self.root)
        self.assertEqual(run(self.root, "--check")[0], 0)
        self.append("tasks", "  - {id: T-9, title: New, status: not-started}")
        self.assertEqual(run(self.root, "--check")[0], 1)

    def test_check_fails_on_validation_error(self):
        run(self.root)
        self.append("tasks", "  - {id: T-9, title: x, status: nope}")
        self.assertEqual(run(self.root, "--check")[0], 1)

    def test_only_the_top_key_may_be_unindented_or_non_entry(self):
        self.append("tasks", "other: 1")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("one line", out)

    def test_task_statuses_come_from_the_registers_enum_and_null_priority_order(self):
        (self.root / "pmo/config.yaml").write_text(
            "schema_version: 1\nvocab: {priority_order: null, my_status: [todo, done]}\nregisters: {tasks: {enums: {status: my_status}}}\n", encoding="utf-8")
        (self.reg / "tasks.yaml").write_text("tasks:\n  - {id: T-1, title: a, status: todo, priority: high}\n", encoding="utf-8")
        self.assertEqual(run(self.root)[0], 0)
        self.assertIn("todo 1, done 0", (self.views / "tasks.md").read_text(encoding="utf-8"))

    def test_register_without_view_or_fields_is_a_clear_error(self):
        (self.root / "pmo/config.yaml").write_text(
            "schema_version: 1\nregisters: {notes: {file: notes.yaml}}\n", encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("register `notes` needs `view`", out)
        self.assertIn("register `notes` needs `fields`", out)

    def test_non_text_id_is_an_error_and_does_not_crash(self):
        self.append("tasks", "  - {id: 5, title: x, status: done}")
        self.append("tasks", "  - {id: [a], title: y, status: done}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("must be text", out)

    def test_view_of_a_removed_register_file(self):
        run(self.root)
        (self.reg / "teams.yaml").unlink()
        code, out = run(self.root, "--check")
        self.assertEqual(code, 1)
        self.assertIn("teams.md (register file is gone)", out)
        self.assertEqual(run(self.root)[0], 0)
        self.assertFalse((self.views / "teams.md").exists())
        self.assertEqual(run(self.root, "--check")[0], 0)

    def test_missing_project_folder(self):
        self.assertEqual(run(self.root / "nope")[0], 2)

    def test_help(self):
        self.assertEqual(run(self.root, "--help")[0], 0)


class CommittedViews(unittest.TestCase):
    def test_acme_views_are_current(self):
        self.assertEqual(run(REPO / "examples/acme", "--check")[0], 0)


if __name__ == "__main__":
    unittest.main()
