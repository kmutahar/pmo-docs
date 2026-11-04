"""Tests for scripts/overdue.py on the Acme fixture. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/pmo-docs/scripts"))
import overdue as od  # noqa: E402


class Overdue(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        shutil.copytree(ROOT / "examples/acme", self.d / "p")
        self.p = self.d / "p"

    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = od.main(["--project", str(self.p), *args])
        return code, out.getvalue()

    def test_acme_as_of(self):
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertIn("| T-1 | Set up staging server | alice | 2026-03-10 | 5 | high |", out)
        self.assertNotIn("T-3", out)  # done
        self.assertNotIn("T-2", out)  # not due yet
        self.assertIn("ACT-1", out)
        self.assertNotIn("ACT-2", out)  # done
        self.assertIn("M-1", out)
        self.assertNotIn("M-2", out)

    def test_days_window(self):
        _, out = self.run_tool("--as-of", "2026-03-15", "--days", "60")
        self.assertIn("M-2", out)

    def test_closed_statuses_come_from_config(self):
        (self.p / "pmo/config.yaml").write_text(
            "schema_version: 1\nregisters: {tasks: {closed: [done, dropped, in-progress]}}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertNotIn("Set up staging", out)

    def test_priority_order_from_config(self):
        (self.p / "pmo/registers/tasks.yaml").write_text(
            "tasks:\n  - {id: T-1, title: a, priority: high, status: blocked, due: 2026-03-01}\n"
            "  - {id: T-2, title: b, priority: low, status: blocked, due: 2026-03-01}\n", encoding="utf-8")
        (self.p / "pmo/config.yaml").write_text("schema_version: 1\nvocab: {priority_order: [low, high]}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("T-2"), out.index("T-1"))

    def test_missing_registers_give_none_rows(self):
        shutil.rmtree(self.p / "pmo/registers")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("| None |"), 5)

    def tasks(self, *lines):
        (self.p / "pmo/registers/tasks.yaml").write_text("tasks:\n" + "".join(f"  - {x}\n" for x in lines), encoding="utf-8")

    def test_bad_and_datetime_due_dates(self):
        self.tasks("{id: T-1, title: a, status: blocked, due: TBD}",
                   "{id: T-2, title: b, status: blocked, due: 2026-03-01 10:00:00}")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertIn("## Bad due dates", out)
        self.assertIn("| tasks | T-1 | TBD |", out)
        self.assertIn("| T-2 | b |", out)

    def test_register_removed_from_config(self):
        (self.p / "pmo/config.yaml").write_text("schema_version: 1\nregisters: {actions: null}\n", encoding="utf-8")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertNotIn("ACT-1", out)

    def test_unreadable_register_exits_2(self):
        (self.p / "pmo/registers/tasks.yaml").write_text("tasks: [\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, _ = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 2)
        self.assertIn("not readable", err.getvalue())

    def test_open_issues_most_severe_first_and_open_risks(self):
        _, out = self.run_tool("--as-of", "2026-03-15")
        a, b = out.index("## Open issues by severity"), out.index("## Open risks")
        issues, risks = out[a:b], out[b:]
        self.assertLess(issues.index("I-3"), issues.index("I-2"))
        self.assertLess(issues.index("I-2"), issues.index("I-1"))
        self.assertNotIn("I-4", issues)  # resolved
        self.assertIn("R-1", risks)
        self.assertNotIn("R-2", risks)  # closed

    def test_milestone_window_is_inclusive_and_sorted(self):
        (self.p / "pmo/registers/milestones.yaml").write_text(
            "milestones:\n  - {id: M-9, title: b, status: not-started, due: 2026-03-29}\n"
            "  - {id: M-8, title: a, status: not-started, due: 2026-03-20}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("M-8"), out.index("M-9"))  # 14 days after 03-15 is 03-29

    def test_missing_project_is_a_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            od.main(["--project", str(self.d / "nope")])
        self.assertEqual(e.exception.code, 2)

    def test_as_of_without_value_is_a_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            od.main(["--as-of"])
        self.assertEqual(e.exception.code, 2)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            od.main(["--as-of", "not-a-date"])
        self.assertEqual(e.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
