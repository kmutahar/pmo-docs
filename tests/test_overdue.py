"""Tests for scripts/overdue.py on the Acme fixture. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True  # importing the shipped scripts must leave no __pycache__
sys.path.insert(0, str(ROOT / "skills/pmo-docs/scripts"))
import overdue as od  # noqa: E402
import pmo_common as pc  # noqa: E402
import render_views as rv  # noqa: E402


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

    def sync_views(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rv.main(["--project", str(self.p)])
        self.assertEqual(code, 0, out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rv.main(["--project", str(self.p), "--check"])
        self.assertEqual(code, 0, out.getvalue())

    def merge_config(self, updates):
        def deep_merge(dst, src):
            for k, v in src.items():
                if isinstance(v, dict) and isinstance(dst.get(k), dict):
                    deep_merge(dst[k], v)
                else:
                    dst[k] = v

        cfg_path = self.p / "pmo/config.yaml"
        cfg = pc.yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        deep_merge(cfg, updates)
        cfg_path.write_text(pc.yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    def replace_task(self, tid, entry):
        path = self.p / "pmo/registers/tasks.yaml"
        lines = path.read_text(encoding="utf-8").splitlines()
        out = [f"  - {entry}" if (f"id: {tid}," in ln or f"id: {tid}}}" in ln) else ln for ln in lines]
        path.write_text("\n".join(out) + "\n", encoding="utf-8")

    def clear_task_refs(self):
        """Blank every T-n reference in the other registers, editing the text so entries stay on one line."""
        def drop_ids(m):
            return "[" + ", ".join(x for x in m.group(1).split(", ") if not re.fullmatch(r"T-\d+", x)) + "]"

        for p in sorted((self.p / "pmo/registers").glob("*.yaml")):
            if p.name == "tasks.yaml":
                continue
            text = p.read_text(encoding="utf-8")
            new = re.sub(r"(\w+): T-\d+\b", r"\1: null", text)
            new = re.sub(r"\[([^\]]*)\]", drop_ids, new)
            if new != text:
                p.write_text(new, encoding="utf-8")

    def test_acme_as_of(self):
        self.sync_views()
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertIn("| T-001 | Set up staging server | alice | 2026-03-10 | 5 | high |", out)
        self.assertNotIn("T-003", out)  # done
        self.assertNotIn("T-002", out)  # not due yet
        self.assertIn("ACT-001", out)
        self.assertNotIn("ACT-002", out)  # done
        self.assertIn("M-001", out)
        self.assertNotIn("M-002", out)

    def test_null_cells_say_not_set(self):
        self.replace_task("T-001", "{id: T-001, title: a, priority: null, owner: null, status: blocked, due: 2026-03-10}")
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertIn("| T-001 | a | not set | 2026-03-10 | 5 | not set |", out)

    def test_days_window(self):
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15", "--days", "60")
        self.assertIn("M-002", out)

    def test_closed_statuses_come_from_config(self):
        self.merge_config({"registers": {"tasks": {"closed": ["done", "dropped", "in-progress"]}}})
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertNotIn("Set up staging", out)

    def test_priority_order_from_config(self):
        self.replace_task("T-001", "{id: T-001, title: a, priority: high, status: blocked, due: 2026-03-01}")
        self.replace_task("T-002", "{id: T-002, title: b, priority: low, status: blocked, due: 2026-03-01}")
        self.merge_config({"vocab": {"priority_order": ["low", "high", "medium"]}})
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("T-002"), out.index("T-001"))

    def test_missing_registers_give_none_rows(self):
        shutil.rmtree(self.p / "pmo/registers")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("| None |"), 7)

    def tasks(self, *lines):
        (self.p / "pmo/registers/tasks.yaml").write_text("tasks:\n" + "".join(f"  - {x}\n" for x in lines), encoding="utf-8")

    def test_bad_and_datetime_due_dates(self):
        self.tasks("{id: T-001, title: a, status: blocked, due: TBD}",
                   "{id: T-002, title: b, status: blocked, due: 2026-03-01 10:00:00}")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertIn("## Bad due dates", out)
        self.assertIn("| tasks | T-001 | TBD |", out)
        self.assertIn("| T-002 | b |", out)

    def test_register_removed_from_config(self):
        self.merge_config({"registers": {"actions": None}})
        self.sync_views()
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertNotIn("ACT-001", out)

    def test_unreadable_register_exits_2(self):
        (self.p / "pmo/registers/tasks.yaml").write_text("tasks: [\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, _ = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 2)
        self.assertIn("not readable", err.getvalue())

    def test_open_issues_most_severe_first_and_open_risks(self):
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15")
        a, b = out.index("## Open issues by severity"), out.index("## Open risks")
        issues, risks = out[a:b], out[b:]
        self.assertLess(issues.index("I-003"), issues.index("I-002"))
        self.assertLess(issues.index("I-002"), issues.index("I-001"))
        self.assertNotIn("I-004", issues)  # resolved
        self.assertIn("R-001", risks)
        self.assertNotIn("R-002", risks)  # closed

    def test_milestone_window_is_inclusive_and_sorted(self):
        ms = self.p / "pmo/registers/milestones.yaml"
        ms.write_text(
            ms.read_text(encoding="utf-8").rstrip("\n") + "\n"
            "  - {id: M-009, title: b, status: not-started, due: 2026-03-29}\n"
            "  - {id: M-008, title: a, status: not-started, due: 2026-03-20}\n",
            encoding="utf-8",
        )
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("M-008"), out.index("M-009"))  # 14 days after 03-15 is 03-29

    def test_blocked_tasks_and_tasks_with_no_due_date_have_their_own_tables(self):
        self.tasks("{id: T-001, title: a, status: blocked, due: 2026-03-01}", "{id: T-002, title: b, status: in-progress}",
                   "{id: T-003, title: c, status: done}", "{id: T-004, title: d, status: not-started, due: TBD}")
        _, out = self.run_tool("--as-of", "2026-03-15")
        blocked = out[out.index("## Blocked tasks"):out.index("## Tasks with no due date")]
        undated = out[out.index("## Tasks with no due date"):out.index("## Bad due dates")]
        self.assertIn("| T-001 | a | not set | 2026-03-01 | not set |", blocked)
        self.assertNotIn("T-002", blocked)
        self.assertIn("| T-002 | b | not set | in-progress | not set |", undated)
        self.assertNotIn("T-003", undated)  # closed
        self.assertNotIn("T-004", undated)  # bad dates are listed under Bad due dates
        self.assertNotIn("T-001", undated)

    def test_blocked_statuses_come_from_config(self):
        self.merge_config({"registers": {"tasks": {"blocked": ["waiting"]}}})
        self.tasks("{id: T-001, title: a, status: blocked, due: 2026-03-20}", "{id: T-002, title: b, status: waiting, due: 2026-03-20}")
        _, out = self.run_tool("--as-of", "2026-03-15")
        blocked = out[out.index("## Blocked tasks"):out.index("## Tasks with no due date")]
        self.assertIn("T-002", blocked)
        self.assertNotIn("T-001", blocked)

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
        self.replace_task("T-001", "{id: T-001, title: a, status: in-progress, due: 2026-03-15}")
        self.replace_task("T-002", "{id: T-002, title: b, status: in-progress, due: 2026-03-14}")
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertNotIn("| T-001 |", out)
        self.assertIn("| T-002 | b | not set | 2026-03-14 | 1 | not set |", out)

    def test_as_of_before_every_due_date_lists_no_overdue_work(self):
        self.sync_views()
        _, out = self.run_tool("--as-of", "2020-01-01")
        self.assertIn("Overdue tasks: 0, open actions past due: 0", out)

    def test_days_late_across_a_leap_day(self):
        self.replace_task("T-001", "{id: T-001, title: a, status: blocked, due: 2024-02-28}")
        self.sync_views()
        self.assertIn("| 2 |", self.run_tool("--as-of", "2024-03-01")[1])  # 28th, 29th
        self.replace_task("T-001", "{id: T-001, title: a, status: blocked, due: 2023-02-28}")
        self.sync_views()
        self.assertIn("| 1 |", self.run_tool("--as-of", "2023-03-01")[1])
        self.assertIn("as of 2024-02-29", self.run_tool("--as-of", "2024-02-29")[1])

    def test_days_zero_keeps_only_milestones_due_by_the_as_of_date(self):
        (self.p / "pmo/registers/milestones.yaml").write_text(
            "milestones:\n  - {id: M-001, title: a, status: not-started, due: 2026-03-14}\n"
            "  - {id: M-002, title: b, status: not-started, due: 2026-03-15}\n"
            "  - {id: M-003, title: c, status: not-started, due: 2026-03-16}\n", encoding="utf-8")
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15", "--days", "0")
        self.assertIn("milestones due within 0 days or overdue: 2", out)
        self.assertNotIn("M-003", out)

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
        self.replace_task("T-001", "{id: T-001, title: \"عنوان | x\", status: blocked, due: 2026-03-01, owner: [alice, bob]}")
        self.sync_views()
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertIn("| T-001 | عنوان \\| x | alice, bob | 2026-03-01 | 14 | not set |", out)

    def test_task_order_is_days_late_then_priority_then_id_and_unknown_priority_last(self):
        self.tasks("{id: T-004, title: d, status: blocked, due: 2026-03-01}",
                   "{id: T-003, title: c, status: blocked, due: 2026-03-01, priority: high}",
                   "{id: T-002, title: b, status: blocked, due: 2026-03-01, priority: bogus}",
                   "{id: T-001, title: a, status: blocked, due: 2026-03-01, priority: high}",
                   "{id: T-000, title: z, status: blocked, due: 2026-02-01, priority: low}")
        _, out = self.run_tool("--as-of", "2026-03-15")
        ids = [out.index(f"| T-{n:03d} |") for n in (0, 1, 3, 2, 4)]
        self.assertEqual(ids, sorted(ids))

    def test_unusable_due_values(self):
        # falsy values mean "not set"; other values that do not parse are listed under Bad due dates
        self.tasks("{id: T-001, title: a, status: blocked, due: \"\"}", "{id: T-002, title: b, status: blocked, due: 0}",
                   "{id: T-003, title: c, status: blocked}", "{id: T-004, title: d, status: blocked, due: true}",
                   "{id: T-005, title: e, status: blocked, due: \"2026-02-30\"}", "{id: T-006, title: f, status: blocked, due: \"15/03/2026\"}")
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        bad = out[out.index("## Bad due dates"):]
        for tid in ("T-004", "T-005", "T-006"):
            self.assertIn(f"| tasks | {tid} |", bad)
        for tid in ("T-001", "T-002", "T-003"):
            self.assertNotIn(f"| tasks | {tid} |", bad)
        self.assertIn("Overdue tasks: 0", out)

    def test_no_bad_due_dates_section_when_all_dates_parse(self):
        self.sync_views()
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
        self.clear_task_refs()
        self.sync_views()
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertIn("Overdue tasks: 0", out)

    def test_issues_without_severity_or_without_severity_vocab_still_list(self):
        (self.p / "pmo/registers/issues.yaml").write_text(
            "issues:\n  - {id: I-002, title: b, status: open}\n  - {id: I-001, title: a, status: open, severity: high}\n"
            "  - {id: I-000, title: z, status: open, severity: unheard-of}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("| I-001 |"), out.index("| I-000 |"))  # a known severity sorts before an unknown one
        self.assertLess(out.index("| I-000 |"), out.index("| I-002 |"))  # ties by id
        (self.p / "pmo/config.yaml").write_text("schema_version: 1\nregisters: {issues: {enums: null}}\n", encoding="utf-8")
        _, out = self.run_tool("--as-of", "2026-03-15")
        self.assertLess(out.index("| I-000 |"), out.index("| I-001 |"))  # no vocab: plain id order

    def test_help_exits_0_and_a_bad_flag_exits_2(self):
        import subprocess
        tool = str(ROOT / "skills/pmo-docs/scripts/overdue.py")
        self.assertEqual(subprocess.run([sys.executable, tool, "--help"], capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run([sys.executable, tool, "--project", str(self.p), "--bogus"], capture_output=True).returncode, 2)

    def test_ids_sort_by_number(self):
        risks_file = self.p / "pmo/registers/risks.yaml"
        rtext = risks_file.read_text(encoding="utf-8")
        r1_line = next(ln for ln in rtext.splitlines() if "id: R-001," in ln or "id: R-001}" in ln)
        risks_file.write_text(
            rtext.rstrip("\n") + "\n" + r1_line.replace("R-001", "R-010") + "\n" + r1_line.replace("R-001", "R-009") + "\n",
            encoding="utf-8",
        )
        tasks_file = self.p / "pmo/registers/tasks.yaml"
        ttext = tasks_file.read_text(encoding="utf-8")
        tasks_file.write_text(
            ttext.rstrip("\n") + "\n"
            "  - {id: T-010, title: Task ten, priority: high, owner: alice, status: in-progress, due: 2026-03-01}\n"
            "  - {id: T-009, title: Task nine, priority: high, owner: alice, status: in-progress, due: 2026-03-01}\n",
            encoding="utf-8",
        )
        self.sync_views()
        code, out = self.run_tool("--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        self.assertLess(out.index("| R-009 |"), out.index("| R-010 |"))
        self.assertLess(out.index("| T-009 |"), out.index("| T-010 |"))


if __name__ == "__main__":
    unittest.main()
