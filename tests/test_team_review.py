"""Tests for scripts/team_review.py on the Acme fixture. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import csv
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True  # importing the shipped scripts must leave no __pycache__
sys.path.insert(0, str(ROOT / "skills/pmo-docs/scripts"))
import team_review as tr  # noqa: E402


class TeamReview(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        shutil.copytree(ROOT / "examples/acme", self.d / "p")
        self.p = self.d / "p"

    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tr.main(["--project", str(self.p), *args])
        return code, out.getvalue()

    def test_markdown_checklist_per_person(self):
        code, out = self.run_tool()
        self.assertEqual(code, 0)
        self.assertIn("## Sam Example (0)\n\n- None\n", out)
        self.assertIn("- [ ] `T-1` Set up staging server (tasks, in-progress, due 2026-03-10)", out)
        self.assertIn("- [ ] `REQ-1` Users can log in (requirements, accepted)", out)
        self.assertIn("- [ ] `ACT-1` Send vendor shortlist (actions, open, due 2026-03-12)", out)
        for closed in ("T-3", "R-2", "I-4", "ACT-2"):
            self.assertNotIn(f"`{closed}`", out)
        self.assertLess(out.index("## Sam Example"), out.index("## Alice Example"))

    def test_csv_one_row_per_entry(self):
        code, out = self.run_tool("--csv")
        self.assertEqual(code, 0)
        rows = list(csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0], ["person", "register", "id", "title", "status", "due"])
        self.assertIn(["Alice Example", "tasks", "T-1", "Set up staging server", "in-progress", "2026-03-10"], rows)
        self.assertIn(["Alice Example", "issues", "I-3", "Login fails on staging", "open", ""], rows)
        self.assertEqual(len(rows), 11)

    def test_no_owner_and_unknown_owner_get_their_own_heading(self):
        path = self.p / "pmo/registers/tasks.yaml"
        path.write_text("tasks:\n  - {id: T-1, title: a, status: open}\n  - {id: T-2, title: b, owner: zed, status: open}\n", encoding="utf-8")
        _, out = self.run_tool()
        self.assertIn("## not set (1)\n\n- [ ] `T-1` a (tasks, open)", out)
        self.assertIn("## zed (1)\n\n- [ ] `T-2` b (tasks, open)", out)

    def test_glossary_proposed_rows_go_to_the_manager(self):
        g = self.p / "pmo/data/glossary-ar.md"
        g.write_text(g.read_text(encoding="utf-8").rstrip("\n").replace("|---|---|---|---|---|", "|---|---|---|---|---|\n| G-019 | Review | مراجعة | T-1 | 2026-03-01 |"), encoding="utf-8")
        code, out = self.run_tool("--csv")
        self.assertEqual(code, 0)
        self.assertIn("Sam Example,glossary-ar,G-019,Review -> مراجعة,proposed,\n", out)
        self.assertNotIn("G-018", out)  # an Approved row

    def test_missing_glossary_and_registers(self):
        (self.p / "pmo/data/glossary-ar.md").unlink()
        (self.p / "pmo/registers/tasks.yaml").unlink()
        code, out = self.run_tool("--csv")
        self.assertEqual(code, 0)
        self.assertNotIn(",tasks,", out)

    def test_unreadable_register_exits_2(self):
        (self.p / "pmo/registers/tasks.yaml").write_text("tasks: [\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, _ = self.run_tool()
        self.assertEqual(code, 2)
        self.assertIn("not readable", err.getvalue())


if __name__ == "__main__":
    unittest.main()
