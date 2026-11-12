"""Tests for scripts/renumber.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_renumber"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "skills/pmo-docs/scripts/renumber.py"
RV = REPO / "skills/pmo-docs/scripts/render_views.py"
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


class TestRenumber(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        self.docs = self.root / "pmo/documents"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_tool(self, *args):
        p = subprocess.run([sys.executable, str(TOOL), "--project", str(self.root), *args],
                           capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout, p.stderr

    def append_entry(self, reg_name, entry_text):
        f = self.reg / f"{reg_name}.yaml"
        text = f.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        f.write_text(text + f"  - {entry_text}\n", encoding="utf-8")

    def test_01_no_arguments_on_clean_acme(self):
        tasks_before = (self.reg / "tasks.yaml").read_bytes()
        code, out, err = self.run_tool()
        self.assertEqual(code, 0, out + err)
        self.assertIn("no duplicate ids", out)
        self.assertEqual((self.reg / "tasks.yaml").read_bytes(), tasks_before)

    def test_02_add_second_t5_dry_run(self):
        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")
        code, out, err = self.run_tool()
        self.assertEqual(code, 1, out + err)
        self.assertIn("duplicate T-5 in pmo/registers/tasks.yaml", out)
        self.assertIn("keeps T-5", out)
        self.assertIn("Write release notes", out)
        self.assertIn("owner alice", out)
        self.assertIn("gets  T-6", out)
        self.assertIn("Fix login timeout", out)
        self.assertIn("owner bob", out)
        self.assertIn("next: renumber.py --apply", out)

    def test_03_apply_with_no_references(self):
        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")

        changes_before = (self.reg / "changes.yaml").read_bytes()

        code, out, err = self.run_tool("--apply")
        self.assertEqual(code, 0, out + err)

        tasks_lines = (self.reg / "tasks.yaml").read_text(encoding="utf-8").splitlines()
        self.assertIn("id: T-5", tasks_lines[-2])
        self.assertIn("id: T-6", tasks_lines[-1])
        self.assertIn("Fix login timeout", tasks_lines[-1])

        self.assertEqual((self.reg / "changes.yaml").read_bytes(), changes_before)

        rv_check = subprocess.run([sys.executable, str(RV), "--project", str(self.root), "--check"],
                                  capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(rv_check.returncode, 0, rv_check.stdout + rv_check.stderr)

    def test_04_references_dry_run_and_apply(self):
        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")
        self.append_entry("changes", "{id: CR-3, title: Dark mode follow up, requested_by: bob, date: 2026-03-08, description: desc, impact: imp, status: proposed, decided_by: null, decided_on: null, related_tasks: [T-5]}")
        self.append_entry("dependencies", "{id: D-3, type: internal, from: T-5, to: T-1, text: release notes need server, status: open}")

        draft_file = self.docs / "draft.md"
        draft_content = (
            "---\n"
            "title: Draft\n"
            "type: status-report\n"
            "project: acme\n"
            "manager: alice\n"
            "period: 2026-03\n"
            "status: draft\n"
            "last_updated: 2026-03-15\n"
            "---\n\n"
            "T-5 is blocked by vendor\n"
        )
        draft_file.write_text(draft_content, encoding="utf-8")

        code, out, err = self.run_tool()
        self.assertEqual(code, 1, out + err)
        self.assertIn("references:", out)
        self.assertIn("pmo/registers/changes.yaml:4", out)
        self.assertIn("CR-3", out)
        self.assertIn("in related_tasks", out)
        self.assertIn("--rewrite pmo/registers/changes.yaml:4=T-6", out)
        self.assertIn("--keep pmo/registers/changes.yaml:4", out)

        self.assertIn("pmo/registers/dependencies.yaml:4", out)
        self.assertIn("D-3", out)
        self.assertIn("in from", out)
        self.assertIn("--rewrite pmo/registers/dependencies.yaml:4=T-6", out)
        self.assertIn("--keep pmo/registers/dependencies.yaml:4", out)

        self.assertIn("pmo/documents/draft.md:11", out)
        self.assertIn("draft", out)
        self.assertIn("T-5 is blocked by vendor", out)
        self.assertIn("next: choose --rewrite or --keep for each reference, then renumber.py --apply <flags>", out)

        code_no_dec, out_no_dec, err_no_dec = self.run_tool("--apply")
        self.assertEqual(code_no_dec, 2)
        self.assertIn("has no decision", out_no_dec + err_no_dec)

        code_apply, out_apply, err_apply = self.run_tool(
            "--apply",
            "--rewrite", "pmo/registers/changes.yaml:4=T-6",
            "--keep", "pmo/registers/dependencies.yaml:4",
            "--keep", "pmo/documents/draft.md:11",
        )
        self.assertEqual(code_apply, 0, out_apply + err_apply)

        changes_text = (self.reg / "changes.yaml").read_text(encoding="utf-8")
        self.assertIn("related_tasks: [T-6]", changes_text)

        deps_text = (self.reg / "dependencies.yaml").read_text(encoding="utf-8")
        self.assertIn("from: T-5", deps_text)

        draft_text = draft_file.read_text(encoding="utf-8")
        self.assertIn("T-5 is blocked by vendor", draft_text)

    def test_05_finished_document_left_alone(self):
        fin_file = self.docs / "Decision log.md"
        fin_before = fin_file.read_bytes()

        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")

        fin_text = fin_file.read_text(encoding="utf-8").replace("status: draft", "status: finished") + "\nMentions T-5 in finished doc\n"
        fin_file.write_text(fin_text, encoding="utf-8")
        fin_after_edit = fin_file.read_bytes()

        code, out, err = self.run_tool()
        self.assertEqual(code, 1, out + err)
        self.assertIn("left alone (finished):", out)
        self.assertIn("pmo/documents/Decision log.md:", out)

        code_app, out_app, err_app = self.run_tool("--apply")
        self.assertEqual(code_app, 0, out_app + err_app)
        self.assertEqual(fin_file.read_bytes(), fin_after_edit)

    def test_06_three_copies_of_t5(self):
        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Update payment gateway, team: web, group: ui, priority: high, owner: bob, status: not-started, due: 2026-03-26, period: 2026-03, notes: ''}")
        self.append_entry("changes", "{id: CR-3, title: Dark mode, requested_by: bob, date: 2026-03-08, description: desc, impact: imp, status: proposed, decided_by: null, decided_on: null, related_tasks: [T-5]}")

        code, out, err = self.run_tool()
        self.assertEqual(code, 1, out + err)
        self.assertIn("keeps T-5", out)
        self.assertIn("gets  T-6", out)
        self.assertIn("gets  T-7", out)
        self.assertIn("--rewrite pmo/registers/changes.yaml:4=T-6", out)
        self.assertIn("--rewrite pmo/registers/changes.yaml:4=T-7", out)

        code_app, out_app, err_app = self.run_tool("--apply", "--rewrite", "pmo/registers/changes.yaml:4=T-7")
        self.assertEqual(code_app, 0, out_app + err_app)

        changes_text = (self.reg / "changes.yaml").read_text(encoding="utf-8")
        self.assertIn("related_tasks: [T-7]", changes_text)

        tasks_text = (self.reg / "tasks.yaml").read_text(encoding="utf-8")
        self.assertIn("id: T-5", tasks_text)
        self.assertIn("id: T-6", tasks_text)
        self.assertIn("id: T-7", tasks_text)

    def test_07_line_makes_second_copy_keeper(self):
        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")

        code, out, err = self.run_tool("--line", "pmo/registers/tasks.yaml:7", "--apply")
        self.assertEqual(code, 0, out + err)

        tasks_lines = (self.reg / "tasks.yaml").read_text(encoding="utf-8").splitlines()
        self.assertTrue(any("id: T-5" in line and "Fix login timeout" in line for line in tasks_lines))
        self.assertTrue(any("id: T-6" in line and "Write release notes" in line for line in tasks_lines))
        self.assertIn("id: T-6", tasks_lines[-1])

    def test_08_prefixes_do_not_bleed(self):
        self.append_entry("decisions", "{id: DEC-2, title: Duplicate decision, status: proposed, decided_by: sam, date: 2026-03-09}")

        deps_before = (self.reg / "dependencies.yaml").read_bytes()

        code, out, err = self.run_tool("DEC-2")
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("dependencies.yaml", out)

        code_app, out_app, err_app = self.run_tool(
            "DEC-2", "--apply",
            "--keep", "pmo/registers/meetings.yaml:2",
            "--keep", "pmo/documents/2026-03 - Status report.md:47",
            "--keep", "pmo/documents/2026-03 - Status report.md:54",
            "--keep", "pmo/documents/Decision log.md:16",
            "--keep", "pmo/documents/Decision log.md:20",
        )
        self.assertEqual(code_app, 0, out_app + err_app)
        self.assertEqual((self.reg / "dependencies.yaml").read_bytes(), deps_before)

    def test_08b_prefixes_a_and_t_do_not_bleed(self):
        self.append_entry("assumptions", "{id: A-1, text: Duplicate assumption, owner: bob, status: open}")
        self.append_entry("tasks", "{id: T-1, title: Duplicate task, team: web, group: ui, priority: low, owner: bob, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        before = {n: (self.reg / f"{n}.yaml").read_bytes() for n in ("actions", "tests", "teams")}

        code, out, err = self.run_tool("A-1")
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("actions.yaml", out)

        code, out, err = self.run_tool("T-1")
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("tests.yaml", out)
        self.assertNotIn("teams.yaml", out)

        code, out, err = self.run_tool("A-1", "--apply")
        self.assertEqual(code, 1, out + err)  # T-1 remains
        for n, b in before.items():
            self.assertEqual((self.reg / f"{n}.yaml").read_bytes(), b, n)

    def test_09_duplicates_in_two_registers_fixed_in_one_apply(self):
        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")
        self.append_entry("milestones", "{id: M-3, title: Beta release, status: not-started, due: 2026-04-15, period: 2026-04}")
        self.append_entry("milestones", "{id: M-3, title: Duplicate beta, status: not-started, due: 2026-04-20, period: 2026-04}")

        code, out, err = self.run_tool("--apply")
        self.assertEqual(code, 0, out + err)

        rv_check = subprocess.run([sys.executable, str(RV), "--project", str(self.root), "--check"],
                                  capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(rv_check.returncode, 0, rv_check.stdout + rv_check.stderr)

    def test_10_id_narrowing_leaves_other_duplicate(self):
        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")
        self.append_entry("milestones", "{id: M-3, title: Beta release, status: not-started, due: 2026-04-15, period: 2026-04}")
        self.append_entry("milestones", "{id: M-3, title: Duplicate beta, status: not-started, due: 2026-04-20, period: 2026-04}")

        code, out, err = self.run_tool("T-5", "--apply")
        self.assertEqual(code, 1, out + err)
        self.assertIn("duplicate id M-3", out + err)

    def test_11_usage_errors(self):
        code, out, err = self.run_tool("T-1")
        self.assertEqual(code, 2)
        self.assertIn("ERROR id T-1 is not duplicated", err + out)

        code, out, err = self.run_tool("--line", "pmo/registers/tasks.yaml:2")
        self.assertEqual(code, 2)
        self.assertIn("holds no duplicate", err + out)

        self.append_entry("tasks", "{id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}")
        self.append_entry("tasks", "{id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}")

        code, out, err = self.run_tool("--apply", "--rewrite", "pmo/registers/tasks.yaml:2=T-6")
        self.assertEqual(code, 2)
        self.assertIn("unknown reference line", err + out)

    def test_12_conflict_markers(self):
        tasks_file = self.reg / "tasks.yaml"
        tasks_before = tasks_file.read_bytes()
        conflict_text = (
            "tasks:\n"
            "<<<<<<< HEAD\n"
            "  - {id: T-5, title: Write release notes, team: platform, group: docs, priority: low, owner: alice, status: not-started, due: 2026-03-28, period: 2026-03, notes: ''}\n"
            "=======\n"
            "  - {id: T-5, title: Fix login timeout, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: ''}\n"
            ">>>>>>> branch\n"
        )
        tasks_file.write_text(conflict_text, encoding="utf-8")

        code, out, err = self.run_tool()
        self.assertEqual(code, 1, out + err)
        self.assertIn("merge conflict markers; resolve them first (references/git.md, Several writers)", out + err)
        self.assertEqual(tasks_file.read_text(encoding="utf-8"), conflict_text)


if __name__ == "__main__":
    unittest.main()
