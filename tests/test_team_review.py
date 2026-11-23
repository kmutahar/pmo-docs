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
        self.assertIn("- [ ] `T-001` Set up staging server (tasks, in-progress, due 2026-03-10)", out)
        self.assertIn("- [ ] `REQ-001` Users can log in (requirements, accepted)", out)
        self.assertIn("- [ ] `ACT-001` Send vendor shortlist (actions, open, due 2026-03-12)", out)
        for closed in ("T-003", "R-002", "I-004", "ACT-002"):
            self.assertNotIn(f"`{closed}`", out)
        self.assertLess(out.index("## Sam Example"), out.index("## Alice Example"))

    def test_csv_one_row_per_entry(self):
        code, out = self.run_tool("--csv")
        self.assertEqual(code, 0)
        rows = list(csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0], ["person", "register", "id", "title", "status", "due", "description", "question"])
        self.assertIn(["Alice Example", "tasks", "T-001", "Set up staging server", "in-progress", "2026-03-10", "", ""], rows)
        self.assertIn(["Alice Example", "issues", "I-003", "Login fails on staging", "open", "", "Users get an error page", ""], rows)
        self.assertEqual(len(rows), 11)

    def test_no_owner_and_unknown_owner_get_their_own_heading(self):
        path = self.p / "pmo/registers/tasks.yaml"
        path.write_text("tasks:\n  - {id: T-001, title: a, status: open}\n  - {id: T-002, title: b, owner: zed, status: open}\n", encoding="utf-8")
        _, out = self.run_tool()
        self.assertIn("## not set (1)\n\n- [ ] `T-001` a (tasks, open)", out)
        self.assertIn("## zed (1)\n\n- [ ] `T-002` b (tasks, open)", out)

    def test_glossary_proposed_rows_go_to_the_manager(self):
        g = self.p / "pmo/data/glossary-ar.md"
        g.write_text(g.read_text(encoding="utf-8").rstrip("\n").replace("|---|---|---|---|---|", "|---|---|---|---|---|\n| G-019 | Review | مراجعة | T-001 | 2026-03-01 |"), encoding="utf-8")
        code, out = self.run_tool("--csv")
        self.assertEqual(code, 0)
        self.assertIn("Sam Example,glossary-ar,G-019,Review -> مراجعة,proposed,,,\n", out)
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

    def test_description_and_question_in_markdown_and_csv(self):
        reg = self.p / "pmo/registers/actions.yaml"
        reg.write_text("actions:\n  - {id: ACT-001, text: Send list, owner: bob, status: open, description: Send the vendor list, question: 'Which vendors?'}\n", encoding="utf-8")
        _, md = self.run_tool()
        self.assertIn("(actions, open) - Send the vendor list\n  - Question: Which vendors?\n", md)
        _, out = self.run_tool("--csv")
        self.assertIn(["Bob Example", "actions", "ACT-001", "Send list", "open", "", "Send the vendor list", "Which vendors?"], list(csv.reader(io.StringIO(out))))

    def test_lang_takes_text_from_the_names_file_and_falls_back(self):
        (self.p / "pmo/registers/actions.yaml").write_text("actions:\n  - {id: ACT-001, text: Send list, owner: bob, status: open, description: English text, question: English question}\n", encoding="utf-8")
        n = self.p / "pmo/data/names-ar.yaml"
        n.write_text("approved:\n  tasks:\n    T-001: {title: عنوان, description: وصف}\n  actions:\n    ACT-001: {question: سؤال}\nproposed:\n  issues:\n    I-003: {description: مقترح}\n", encoding="utf-8")
        _, out = self.run_tool("--csv", "--lang", "ar")
        rows = list(csv.reader(io.StringIO(out)))
        self.assertEqual(next(r for r in rows if r[2] == "T-001")[6], "وصف")
        self.assertEqual(next(r for r in rows if r[2] == "I-003")[6], "مقترح")  # proposed text counts
        act = next(r for r in rows if r[2] == "ACT-001")
        self.assertEqual(act[6:], ["English text", "سؤال"])  # description falls back, question translated
        n.write_text("approved:\n  tasks:\n    T-001: {title: عنوان}\n", encoding="utf-8")
        _, out = self.run_tool("--csv", "--lang", "ar")
        self.assertEqual(next(r for r in csv.reader(io.StringIO(out)) if r[2] == "T-001")[6], "عنوان")  # translated title stands in

    def test_lang_must_be_a_translation_language(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            self.run_tool("--lang", "fr")
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("not a translation language", err.getvalue())

    def import_csv(self, text, *args):
        f = self.d / "review.csv"
        f.write_text(text, encoding="utf-8")
        before = {x: x.read_bytes() for x in (self.p / "pmo/registers").iterdir()}
        code, out = self.run_tool("--import", str(f), *args)
        self.assertEqual(before, {x: x.read_bytes() for x in (self.p / "pmo/registers").iterdir()})  # writes nothing
        return code, out

    def test_import_proposes_changes_and_writes_nothing(self):
        code, out = self.import_csv(
            "person,register,id,done,answer\n"
            "Alice Example,tasks,T-001,x,Finished on Monday\n"
            "Alice Example,issues,I-003,no,Needs a log\n"
            "Bob Example,actions,ACT-002,yes,\n"  # already done
            "Bob Example,tasks,T-099,1,\n"  # unknown
            "Sam Example,glossary-ar,G-019,x,\n"  # not a register
            "Sam Example,risks,R-001,,\n")
        self.assertEqual(code, 0)
        self.assertIn("## Status changes (1)\n\n- `T-001` (tasks): in-progress -> done; answer: Finished on Monday\n", out)
        self.assertIn("## Answers only (status unchanged) (1)\n\n- `I-003` (issues): open -> open; answer: Needs a log\n", out)
        self.assertIn("## Already at the proposed status (1)\n\n- `ACT-002` (actions): done -> done\n", out)
        self.assertIn("## Unknown ids (1)\n\n- `T-099` (tasks)\n", out)
        self.assertIn("## Skipped (not a register with a done status) (1)\n\n- `G-019` (glossary-ar)\n", out)
        self.assertIn("## No answer and not done (1)", out)

    def test_import_uses_the_registers_closed_status_when_it_has_no_done_list(self):
        _, out = self.import_csv("register,id,done\nissues,I-003,x\n")
        self.assertIn("- `I-003` (issues): open -> resolved", out)

    def test_import_rejects_a_file_without_register_and_id_columns(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            self.import_csv("person,title\nx,y\n")
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("`register` and `id`", err.getvalue())

    def test_import_cannot_be_combined_with_csv(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            self.import_csv("register,id\ntasks,T-001\n", "--csv")
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
