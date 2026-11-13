"""Edge-case tests for scripts/generate.py (usage errors, periods, week start, helpers, odd registers) on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_generate_edges"""
import contextlib
import datetime
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
import generate as gen  # noqa: E402
import pmo_common as pc  # noqa: E402


def run(project, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = gen.main(["--project", str(project), *args])
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class Helpers(unittest.TestCase):
    def test_id_number(self):
        for v, want in (("T-12", 12), ("T-007", 7), ("T-", 0), ("T", 0), ("T-x", 0), (None, 0), (5, 0), ("A-B-3", 3), ("T-12b", 12), ("", 0)):
            self.assertEqual(gen.id_number(v), want, v)

    def test_majority_month_follows_the_fourth_day(self):
        d = datetime.date
        self.assertEqual(gen.majority_month((d(2026, 2, 23), d(2026, 3, 1))), "2026-02")
        self.assertEqual(gen.majority_month((d(2026, 2, 26), d(2026, 3, 4))), "2026-03")  # 3 days Feb, 4 days Mar
        self.assertEqual(gen.majority_month((d(2025, 12, 29), d(2026, 1, 4))), "2026-01")  # year boundary
        self.assertEqual(gen.majority_month((d(2024, 2, 26), d(2024, 3, 3))), "2024-02")  # leap year
        self.assertEqual(gen.majority_month((d(2026, 3, 1), d(2026, 3, 31))), "2026-03")  # a month window

    def test_format_id_list(self):
        self.assertEqual(gen.format_id_list(None), "none")
        self.assertEqual(gen.format_id_list([]), "none")
        self.assertEqual(gen.format_id_list([None, ""]), "none")
        self.assertEqual(gen.format_id_list("D-1"), "`D-1`")
        self.assertEqual(gen.format_id_list(["D-1", "D-2"]), "`D-1`, `D-2`")
        self.assertEqual(gen.format_id_list(("D-1", 2)), "`D-1`, `2`")

    def test_sort_key_priority_then_due_then_id(self):
        key = gen.task_sort_key_for({"vocab": {"priority_order": ["high", "low"]}})
        tasks = [
            {"id": "T-3", "priority": "low", "due": "2026-01-01"},
            {"id": "T-2", "priority": "high"},
            {"id": "T-1", "priority": "high", "due": "2026-05-01"},
            {"id": "T-4", "priority": "weird", "due": "2026-01-01"},
            {"id": "T-5"},
            {"id": "T-10", "priority": "high", "due": "2026-05-01"},
        ]
        self.assertEqual([t["id"] for t in sorted(tasks, key=key)], ["T-1", "T-10", "T-2", "T-3", "T-5", "T-4"])  # unknown priorities last, by name

    def test_sort_key_without_a_priority_vocab(self):
        key = gen.task_sort_key_for({})
        self.assertEqual([t["id"] for t in sorted([{"id": "T-2", "due": "2026-02-01"}, {"id": "T-1"}, {"id": "T-3", "due": "2026-01-01"}], key=key)],
                         ["T-3", "T-2", "T-1"])

    def test_partition_matches_team_id_or_heading_ignoring_case(self):
        teams = [{"id": "b", "heading": "Back End", "order": 2}, {"id": "a", "heading": "Front", "order": 1}, {"id": "c"}]
        tasks = [{"id": "T-1", "team": "A"}, {"id": "T-2", "team": " back end "}, {"id": "T-3", "team": "zzz"}, {"id": "T-4"}, {"id": "T-5", "team": ""}]
        ordered, by_team, none = gen.partition_tasks_by_team(tasks, teams)
        self.assertEqual([t["id"] for t in ordered], ["a", "b", "c"])
        self.assertEqual({k: [t["id"] for t in v] for k, v in by_team.items()}, {"a": ["T-1"], "b": ["T-2"], "c": []})
        self.assertEqual([t["id"] for t in none], ["T-3", "T-4", "T-5"])

    def test_partition_with_no_teams(self):
        self.assertEqual(gen.partition_tasks_by_team([{"id": "T-1", "team": "a"}], []), ([], {}, [{"id": "T-1", "team": "a"}]))

    def test_extract_comments(self):
        self.assertEqual(gen.extract_comments("a <!-- one --> b <!--\ntwo\n-->"), "<!-- one -->\n\n<!--\ntwo\n-->")
        self.assertEqual(gen.extract_comments("no comments"), "")


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.docs = self.root / "pmo/documents"
        self.cfg = self.root / "pmo/config.yaml"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def add_config(self, text):
        self.cfg.write_text(self.cfg.read_text(encoding="utf-8") + text, encoding="utf-8")

    def test_missing_project_folder_exits_2(self):
        code, _, err = run(self.root / "nope", "decision-log")
        self.assertEqual(code, 2)
        self.assertIn("project folder not found", err)

    def test_no_arguments_and_bad_flag_exit_2(self):
        self.assertEqual(run(self.root)[0], 2)
        self.assertEqual(run(self.root, "decision-log", "--nope")[0], 2)

    def test_bad_as_of_exits_2(self):
        for bad in ("2026-02-30", "2026-13-01", "x", "2026-3-1"):
            code, _, err = run(self.root, "status-report", "--stdout", "--as-of", bad)
            self.assertEqual(code, 2, bad)

    def test_bad_period_exits_2_and_writes_nothing(self):
        before = sorted(p.name for p in self.docs.iterdir())
        for bad in ("2026-13", "2026-00", "2026-W00", "2026-W54", "2025-W53", "26-03", "March", "2026-3", "2026-W1"):
            code, _, err = run(self.root, "status-report", bad)
            self.assertEqual(code, 2, bad)
        self.assertEqual(sorted(p.name for p in self.docs.iterdir()), before)

    def test_week_flag_and_explicit_period(self):
        code, out, err = run(self.root, "status-report", "--week", "--as-of", "2026-03-11", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("2026-W11", out)

    def test_week_flag_at_year_boundaries(self):
        # 2027-01-01 is a Friday in ISO week 2026-W53; 2025-12-29 is the Monday of 2026-W01
        for as_of, week in (("2027-01-01", "2026-W53"), ("2025-12-29", "2026-W01"), ("2024-12-30", "2025-W01")):
            code, out, err = run(self.root, "status-report", "--week", "--as-of", as_of, "--stdout")
            self.assertEqual(code, 0, err)
            self.assertIn(week, out, as_of)

    def test_month_period_in_a_leap_year(self):
        code, out, err = run(self.root, "status-report", "2024-02", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("2024-02", out)

    def test_as_of_before_and_after_the_period(self):
        for as_of in ("2020-01-01", "2030-12-31"):
            code, out, err = run(self.root, "status-report", "2026-03", "--as-of", as_of, "--stdout")
            self.assertEqual(code, 0, err)
            self.assertIn(as_of, out)

    def test_week_start_sunday_changes_the_window(self):
        a = run(self.root, "status-report", "2026-W11", "--stdout")[1]
        text = self.cfg.read_text(encoding="utf-8").replace("project:\n", "project:\n  week_start: sunday\n", 1)
        self.cfg.write_text(text, encoding="utf-8")
        code, b, err = run(self.root, "status-report", "2026-W11", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertNotEqual(a, b)

    def test_bad_week_start_exits_2(self):
        text = self.cfg.read_text(encoding="utf-8").replace("project:\n", "project:\n  week_start: someday\n", 1)
        self.cfg.write_text(text, encoding="utf-8")
        code, _, err = run(self.root, "status-report", "--stdout")
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_existing_document_is_never_overwritten_but_stdout_still_works(self):
        target = self.docs / "Decision log.md"
        self.assertTrue(target.exists())
        before = target.read_bytes()
        code, _, err = run(self.root, "decision-log")
        self.assertEqual(code, 3)
        self.assertIn("already exists", err)
        self.assertEqual(target.read_bytes(), before)
        code, out, _ = run(self.root, "decision-log", "--stdout")
        self.assertEqual(code, 0)
        self.assertTrue(out)
        self.assertEqual(target.read_bytes(), before)

    def test_writes_a_new_document_and_creates_the_folder(self):
        shutil.rmtree(self.docs)
        code, out, err = run(self.root, "decision-log")
        self.assertEqual(code, 0, err)
        self.assertIn("wrote ", out)
        self.assertEqual(len(list(self.docs.glob("*.md"))), 1)
        # a second run is refused (exit 3), the first file untouched
        self.assertEqual(run(self.root, "decision-log")[0], 3)

    def test_unknown_type_lists_known_types(self):
        code, _, err = run(self.root, "nope")
        self.assertEqual(code, 2)
        self.assertIn("known types", err)
        self.assertIn("decision-log", err)

    def test_a_type_with_generator_true_but_no_generator_function_exits_2(self):
        self.add_config("\ndoc_types:\n  roadmap:\n    generator: true\n")
        code, _, err = run(self.root, "roadmap")
        self.assertEqual(code, 2)
        self.assertIn("no generator configured", err)

    def test_missing_template_exits_2(self):
        self.add_config("\ndoc_types:\n  decision-log:\n    template: nope.md\n")
        code, _, err = run(self.root, "decision-log", "--stdout")
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_template_name_that_leaves_the_project_exits_2(self):
        self.add_config("\ndoc_types:\n  decision-log:\n    template: ../../../etc/hostname\n")
        code, _, err = run(self.root, "decision-log", "--stdout")
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_config_errors_exit_2_before_any_write(self):
        self.add_config("\nregisters:\n  tasks: {file: ../outside.yaml}\n")
        before = sorted(p.name for p in self.docs.iterdir())
        code, _, err = run(self.root, "status-report", "2026-06")
        self.assertEqual(code, 2)
        self.assertEqual(sorted(p.name for p in self.docs.iterdir()), before)

    def test_unicode_rtl_and_pipe_in_a_task_title_reach_the_report(self):
        reg = self.root / "pmo/registers/tasks.yaml"
        reg.write_text(reg.read_text(encoding="utf-8").replace("Set up staging server", "\u0645\u0647\u0645\u0629 \u2713 a|b"), encoding="utf-8")
        code, out, err = run(self.root, "status-report", "2026-03", "--as-of", "2026-03-20", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("\u0645\u0647\u0645\u0629 \u2713", out)

    def test_empty_task_register_breaks_the_references_to_it(self):
        (self.root / "pmo/registers/tasks.yaml").write_text("", encoding="utf-8")
        before = sorted(p.name for p in self.docs.iterdir())
        code, _, err = run(self.root, "status-report", "2026-06")
        self.assertEqual(code, 1)
        self.assertIn("is not an id in tasks", err)
        self.assertEqual(sorted(p.name for p in self.docs.iterdir()), before)

    def test_every_generator_runs_with_no_entries_in_any_register(self):
        for f in (self.root / "pmo/registers").glob("*.yaml"):
            f.write_text("", encoding="utf-8")
        for t in ("status-report", "project-plan", "team-checklist", "decision-log"):
            code, out, err = run(self.root, t, "--stdout")
            self.assertEqual(code, 0, (t, err))
            self.assertTrue(out.startswith("---\n"), t)

    def test_invalid_register_yaml_exits_1(self):
        (self.root / "pmo/registers/tasks.yaml").write_text("- id: T-1\n  title: [unclosed\n", encoding="utf-8")
        code, _, err = run(self.root, "status-report", "2026-06", "--stdout")
        self.assertEqual(code, 1)
        self.assertIn("ERROR", err)

    def test_dropped_task_is_not_done(self):
        tasks_file = self.root / "pmo/registers/tasks.yaml"
        tasks_text = tasks_file.read_text(encoding="utf-8")
        tasks_file.write_text(tasks_text.replace("status: not-started", "status: dropped", 1), encoding="utf-8")

        code, out, err = run(self.root, "status-report", "2026-03", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("1/3 tasks done (33%)", out)
        self.assertIn("**Progress:** 1/3 tasks done (33%)", out)
        self.assertIn("| medium | 0 / 1 |", out)
        self.assertIn("| Web | 0 / 1 |", out)

        code_chk, out_chk, err_chk = run(self.root, "team-checklist", "2026-03", "--stdout")
        self.assertEqual(code_chk, 0, err_chk)
        t2_lines = [ln for ln in out_chk.splitlines() if "`T-2`" in ln]
        self.assertTrue(t2_lines)
        self.assertFalse(any(ln.strip().startswith("- [x]") for ln in t2_lines))
        self.assertTrue(any(ln.strip().startswith("- [ ]") for ln in t2_lines))

    def test_blocked_task_of_an_earlier_period_is_listed(self):
        code, out, err = run(self.root, "status-report", "--week", "--as-of", "2026-03-31", "--stdout")
        self.assertEqual(code, 0, err)
        blockers_section = out.split("## Blockers and decisions needed")[1].split("## ")[0]
        self.assertIn("T-4", blockers_section)
        progress_line = [ln for ln in out.splitlines() if ln.startswith("**Progress:**")][0]
        self.assertIn("0/0 tasks done (0%)", progress_line)
        priority_section = out.split("## Progress by priority")[1].split("## Planned next")[0]
        self.assertNotIn("T-4", priority_section)

    def test_name_with_dotdot_exits_2(self):
        self.add_config("\ndoc_types:\n  decision-log:\n    name: '../../../escaped-{title}.md'\n")
        escaped_file = self.root.parent / "escaped-Decision log.md"
        code, _, err = run(self.root, "decision-log")
        self.assertEqual(code, 2)
        self.assertIn("ERROR config", err)
        self.assertFalse(escaped_file.exists())

    def test_dangling_symlink_document_is_refused(self):
        target = self.docs / "Decision log.md"
        if target.exists():
            target.unlink()
        outside_target = self.root.parent / "outside_decision_log.md"
        if outside_target.exists():
            outside_target.unlink()
        target.symlink_to(outside_target)
        code, out, err = run(self.root, "decision-log")
        self.assertEqual(code, 2)
        self.assertIn("must stay inside the project", err)
        self.assertFalse(outside_target.exists())


class Odd(unittest.TestCase):
    """Registers with entries the Acme data does not have: missing fields, odd shapes, dates outside the period."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        for name in ("requirements", "tests"):  # they point at tasks, and tasks point back at tests
            self.put(name, "")
        tasks = self.reg / "tasks.yaml"
        tasks.write_text(re.sub(r", tests: \[[^\]]*\]", "", tasks.read_text(encoding="utf-8")), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def put(self, name, text):
        (self.reg / f"{name}.yaml").write_text(text, encoding="utf-8")

    def gen(self, *args):
        code, out, err = run(self.root, *args, "--stdout")
        self.assertEqual(code, 0, err)
        return out, err

    def test_tasks_with_no_team_no_group_no_priority_or_unknown_priority(self):
        self.put("tasks", "tasks:\n"
                 "  - {id: T-1, title: Lone, status: not-started, period: 2026-03}\n"
                 "  - {id: T-2, title: Odd team, team: ghost, group: g1, status: not-started, period: 2026-03}\n"
                 "  - {id: T-3, title: Known, team: platform, priority: high, status: not-started, period: 2026-03}\n")
        plan, _ = self.gen("project-plan", "2026-03")
        self.assertIn("### No team - not set", plan)
        no_team = plan[plan.index("### No team"):]
        self.assertLess(no_team.index("**g1**"), no_team.index("**no group**"))  # "no group" sorts last
        self.assertIn("- Lone `T-1`", plan)
        report, _ = self.gen("status-report", "2026-03")
        self.assertIn("| not set | 0 / 2 | 0 | 0 |", report)  # T-1 and T-2 have no priority
        self.assertIn("| No team | 0 / 2 | 0 | 0 |", report)

    def test_team_without_tasks_is_left_out_of_the_checklist(self):
        self.put("tasks", "tasks:\n  - {id: T-1, title: A, team: platform, status: not-started, period: 2026-03}\n")
        for t in ("project-plan", "team-checklist"):
            out, _ = self.gen(t, "2026-03")
            self.assertIn("Platform", out)
            self.assertNotIn("### Web", out)

    def test_tasks_dated_only_by_due_are_counted_by_the_window(self):
        self.put("tasks", "tasks:\n"
                 "  - {id: T-1, title: In week, status: not-started, due: 2026-03-11}\n"
                 "  - {id: T-2, title: Next week, status: not-started, due: 2026-03-18}\n"
                 "  - {id: T-4, title: Undated, status: not-started}\n")
        out, err = self.gen("status-report", "2026-W11")
        self.assertIn("`T-1`", out)
        self.assertNotIn("`T-2`", out)
        self.assertIn("1 tasks have no period or due date: T-4", err)

    def test_more_than_ten_unplaced_tasks_are_summarised(self):
        rows = "".join(f"  - {{id: T-{i}, title: x, status: not-started}}\n" for i in range(1, 13))
        self.put("tasks", "tasks:\n" + rows)
        _, err = self.gen("status-report", "2026-03")
        self.assertIn("12 tasks have no period or due date: T-1, T-2, T-3, T-4, T-5, T-6, T-7, T-8, T-9, T-10, and 2 more", err)

    def test_done_tasks_from_earlier_periods_are_counted_before(self):
        self.put("tasks", "tasks:\n"
                 "  - {id: T-1, title: a, status: done, period: 2026-01}\n"
                 "  - {id: T-2, title: b, status: done, due: 2026-02-10}\n"
                 "  - {id: T-3, title: c, status: done}\n"
                 "  - {id: T-4, title: d, status: done, period: 2026-03}\n"
                 "  - {id: T-5, title: e, status: done, period: 2026-04}\n")
        out, _ = self.gen("status-report", "2026-03")
        self.assertIn("completed before 2026-03: 2.", out)

    def test_milestones_by_period_by_due_and_closed_ones(self):
        self.put("milestones", "milestones:\n"
                 "  - {id: M-1, title: By period, period: 2026-03, status: done}\n"
                 "  - {id: M-2, title: By due, due: 2026-03-31, status: not-started}\n"
                 "  - {id: M-3, title: Outside, due: 2026-05-31, status: not-started}\n"
                 "  - {id: M-5, title: Undated, status: not-started}\n")
        out, _ = self.gen("team-checklist", "2026-03")
        self.assertIn("- [x] By period `M-1`", out)
        self.assertIn("- [ ] By due `M-2`", out)
        for gone in ("M-3", "M-5"):
            self.assertNotIn(gone, out)
        self.put("milestones", "milestones: []\n")
        self.assertIn("- None", self.gen("team-checklist", "2026-03")[0])

    def test_status_report_milestones_use_the_14_day_look_ahead(self):
        # window 2026-W11 is 9-15 March; the cutoff is 29 March
        self.put("milestones", "milestones:\n"
                 "  - {id: M-1, title: Soon, due: 2026-03-29, status: not-started}\n"
                 "  - {id: M-2, title: Later, due: 2026-03-30, status: not-started}\n"
                 "  - {id: M-3, title: Done in week, due: 2026-03-10, status: done}\n"
                 "  - {id: M-4, title: Done outside, due: 2026-03-20, status: done}\n"
                 "  - {id: M-5, title: Overdue, due: 2025-01-01, status: not-started}\n")
        out, _ = self.gen("status-report", "2026-W11")
        ms = out[out.index("## Milestones"):out.index("## Notes on data")]
        for want in ("M-1", "M-3", "M-5"):
            self.assertIn(want, ms)
        for gone in ("M-2", "M-4"):
            self.assertNotIn(gone, ms)

    def test_decision_shapes(self):
        self.put("decisions", "decisions:\n"
                 "  - {id: DEC-1, status: accepted, options: one, supersedes: DEC-0, related: [DEC-2, null], date: 2026-03-01}\n"
                 "  - {id: DEC-2, status: proposed, options: [], consequences: x, supersedes: [DEC-1], date: 2026-03-02}\n"
                 "  - {id: DEC-3, status: proposed}\n")
        out, _ = self.gen("decision-log")
        self.assertIn("`DEC-0`, `DEC-2`", out)
        self.assertIn("`DEC-1`", out)
        self.assertIn("not recorded", out)
        self.assertEqual(out.count("DEC-3"), out.count("DEC-3"))

    def test_priority_goals_as_text_as_list_and_missing(self):
        self.put("priorities", "priorities:\n"
                 "  - {id: P-1, status: done, title: Text goal, goals: Ship it}\n"
                 "  - {id: P-2, status: done, title: List goal, goals: [A, null, B]}\n"
                 "  - {id: P-3, status: done, title: No goal}\n"
                 "  - {id: P-10, status: done, title: Last}\n")
        out, _ = self.gen("project-plan")
        self.assertIn("- Ship it", out)
        self.assertIn("- A\n- B", out)
        self.assertIn("- not recorded", out)
        self.assertLess(out.index("P-3"), out.index("P-10"))

    def test_roster_entries_without_role_or_name(self):
        with open(self.reg / "roster.yaml", "a", encoding="utf-8") as f:
            f.write("  - {slug: a-b}\n  - {role: Lead}\n")
        out, _ = self.gen("project-plan")
        self.assertIn("| not set | a-b |", out)
        self.assertIn("| Lead | not set |", out)

    def test_changes_and_decisions_outside_the_week_are_left_out(self):
        self.put("changes", "changes:\n  - {id: CR-1, title: In, status: proposed, date: 2026-03-09}\n  - {id: CR-2, title: Out, status: proposed, date: 2026-03-16}\n  - {id: CR-3, title: No date, status: proposed}\n")
        out, _ = self.gen("status-report", "2026-W11")
        section = out[out.index("## Decisions and changes"):out.index("## Risks")]
        self.assertIn("CR-1", section)
        self.assertNotIn("CR-2", section)
        self.assertNotIn("CR-3", section)


if __name__ == "__main__":
    unittest.main()
