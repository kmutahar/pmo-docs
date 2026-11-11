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

    def test_null_cells_say_not_set(self):
        (self.p / "pmo/registers/tasks.yaml").write_text(
            "tasks:\n  - {id: T-1, title: a, priority: null, owner: null, status: blocked, due: 2026-03-10}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertIn("| T-1 | a | not set | 2026-03-10 | 5 | not set |", out)

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

    def test_due_on_the_as_of_date_is_not_overdue_and_the_day_before_is_one_day_late(self):
        self.tasks("{id: T-1, title: a, status: blocked, due: 2026-03-15}", "{id: T-2, title: b, status: blocked, due: 2026-03-14}")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertNotIn("| T-1 |", out)
        self.assertIn("| T-2 | b | not set | 2026-03-14 | 1 | not set |", out)

    def test_as_of_before_every_due_date_lists_no_overdue_work(self):
        _, out = self.run_tool("--as-of", "2020-01-01")
        self.assertIn("Overdue tasks: 0, open actions past due: 0", out)

    def test_days_late_across_a_leap_day(self):
        self.tasks("{id: T-1, title: a, status: blocked, due: 2024-02-28}")
        self.assertIn("| 2 |", self.run_tool("--as-of", "2024-03-01")[1])  # 28th, 29th
        self.tasks("{id: T-1, title: a, status: blocked, due: 2023-02-28}")
        self.assertIn("| 1 |", self.run_tool("--as-of", "2023-03-01")[1])
        self.assertIn("as of 2024-02-29", self.run_tool("--as-of", "2024-02-29")[1])

    def test_days_zero_keeps_only_milestones_due_by_the_as_of_date(self):
        (self.p / "pmo/registers/milestones.yaml").write_text(
            "milestones:\n  - {id: M-1, title: a, status: not-started, due: 2026-03-14}\n"
            "  - {id: M-2, title: b, status: not-started, due: 2026-03-15}\n"
            "  - {id: M-3, title: c, status: not-started, due: 2026-03-16}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15", "--days", "0")
        self.assertIn("milestones due within 0 days or overdue: 2", out)
        self.assertNotIn("M-3", out)

    def test_days_must_be_an_integer(self):
        for bad in ("x", "1.5", ""):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
                od.main(["--project", str(self.p), "--days", bad])
            self.assertEqual(e.exception.code, 2)

    def test_negative_days_is_a_usage_error(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as e:
            od.main(["--project", str(self.p), "--days", "-1"])
        self.assertEqual(e.exception.code, 2)
        self.assertIn("--days cannot be negative", err.getvalue())

    def test_unicode_pipe_and_list_cells(self):
        self.tasks("{id: T-1, title: \"عنوان | x\", status: blocked, due: 2026-03-01, owner: [alice, bob]}")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertIn("| T-1 | عنوان \\| x | alice, bob | 2026-03-01 | 14 | not set |", out)

    def test_task_order_is_days_late_then_priority_then_id_and_unknown_priority_last(self):
        self.tasks("{id: T-4, title: d, status: blocked, due: 2026-03-01}",
                   "{id: T-3, title: c, status: blocked, due: 2026-03-01, priority: high}",
                   "{id: T-2, title: b, status: blocked, due: 2026-03-01, priority: bogus}",
                   "{id: T-1, title: a, status: blocked, due: 2026-03-01, priority: high}",
                   "{id: T-0, title: z, status: blocked, due: 2026-02-01, priority: low}")
        _, out = self.run_tool("--as-of", "2026-03-15")
        ids = [out.index(f"| T-{n} |") for n in (0, 1, 3, 2, 4)]
        self.assertEqual(ids, sorted(ids))

    def test_unusable_due_values(self):
        # falsy values mean "not set"; other values that do not parse are listed under Bad due dates
        self.tasks("{id: T-1, title: a, status: blocked, due: \"\"}", "{id: T-2, title: b, status: blocked, due: 0}",
                   "{id: T-3, title: c, status: blocked}", "{id: T-4, title: d, status: blocked, due: true}",
                   "{id: T-5, title: e, status: blocked, due: \"2026-02-30\"}", "{id: T-6, title: f, status: blocked, due: \"15/03/2026\"}")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        bad = out[out.index("## Bad due dates"):]
        for tid in ("T-4", "T-5", "T-6"):
            self.assertIn(f"| tasks | {tid} |", bad)
        for tid in ("T-1", "T-2", "T-3"):
            self.assertNotIn(f"| tasks | {tid} |", bad)
        self.assertIn("Overdue tasks: 0", out)

    def test_no_bad_due_dates_section_when_all_dates_parse(self):
        self.assertNotIn("Bad due dates", self.run_tool("--as-of", "2026-03-15")[1])

    def test_entry_without_an_id_does_not_crash(self):
        self.tasks("{title: a, status: blocked, due: 2026-03-01}")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertIn("| not set | a |", out)

    def test_register_shapes_that_are_not_a_list_of_maps_exit_2(self):
        for text in ("tasks: [a, b]\n", "tasks: {a: 1}\n", "tasks: x\n", "- a\n"):
            with self.subTest(text=text):
                (self.p / "pmo/registers/tasks.yaml").write_text(text, encoding="utf-8")
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code, _ = self.run_tool("--as-of", "2026-03-15")
                self.assertEqual(code, 2)
                self.assertIn("not readable", err.getvalue())

    def test_empty_register_file_counts_as_empty(self):
        (self.p / "pmo/registers/tasks.yaml").write_text("", encoding="utf-8")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertIn("Overdue tasks: 0", out)

    def test_issues_without_severity_or_without_severity_vocab_still_list(self):
        (self.p / "pmo/registers/issues.yaml").write_text(
            "issues:\n  - {id: I-2, title: b, status: open}\n  - {id: I-1, title: a, status: open, severity: high}\n"
            "  - {id: I-0, title: z, status: open, severity: unheard-of}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("| I-1 |"), out.index("| I-0 |"))  # a known severity sorts before an unknown one
        self.assertLess(out.index("| I-0 |"), out.index("| I-2 |"))  # ties by id
        (self.p / "pmo/config.yaml").write_text("schema_version: 1\nregisters: {issues: {enums: null}}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("| I-0 |"), out.index("| I-1 |"))  # no vocab: plain id order

    def test_help_exits_0_and_a_bad_flag_exits_2(self):
        import subprocess
        tool = str(ROOT / "skills/pmo-docs/scripts/overdue.py")
        self.assertEqual(subprocess.run([sys.executable, tool, "--help"], capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run([sys.executable, tool, "--project", str(self.p), "--bogus"], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
