"""Tests for scripts/pmo_common.py. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import datetime
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


class Common(unittest.TestCase):
    def project(self, config=None, register=None):
        d = Path(tempfile.mkdtemp())
        (d / "pmo/registers").mkdir(parents=True)
        if config is not None:
            (d / "pmo/config.yaml").write_text(config, encoding="utf-8")
        else:
            (d / "pmo/config.yaml").write_text("schema_version: 1\n", encoding="utf-8")
        if register:
            (d / "pmo/registers/tasks.yaml").write_text(register, encoding="utf-8")
        return d

    def test_default_config_is_consistent(self):
        c = pc.load_config(self.project())
        self.assertEqual(c["schema_version"], 1)
        for t in c["doc_types"].values():
            for g in t["generated_from"]:
                self.assertIn(g, c["registers"])
        for r in c["registers"].values():
            for v in r.get("enums", {}).values():
                if "." in v:
                    node = c
                    for part in v.split("."):
                        node = node.get(part) if isinstance(node, dict) else None
                    self.assertIsInstance(node, list)
                else:
                    self.assertIn(v, c["vocab"])

    def test_paths_that_leave_the_project_exit_2(self):
        for cfg in ("registers: {tasks: {view: ../x.md}}\n", "registers: {tasks: {file: ../x.yaml}}\n",
                    "paths: {views: /abs}\n", "paths: {documents: ../../docs}\n"):
            d = self.project("schema_version: 1\n" + cfg, "tasks: []\n")
            with self.assertRaises(SystemExit) as cm:
                pc.load_config(d)
            self.assertEqual(cm.exception.code, 2, cfg)

    def test_render_views_touches_nothing_outside_the_project(self):
        d = self.project("schema_version: 1\nregisters: {tasks: {view: ../victim.md}}\n", "tasks: []\n")
        victim = d.parent / "victim.md"
        victim.write_text("keep", encoding="utf-8")
        for _ in range(2):
            p = subprocess.run([sys.executable, str(pc.SKILL / "scripts/render_views.py"), "--project", str(d)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual(victim.read_text(encoding="utf-8"), "keep")
        victim.unlink()

    def render(self, d):
        return subprocess.run([sys.executable, str(pc.SKILL / "scripts/render_views.py"), "--project", str(d)],
                              capture_output=True, text=True, encoding="utf-8")

    def test_symlinks_out_of_the_project_exit_2(self):
        outside = Path(tempfile.mkdtemp())
        (outside / "tasks.md").write_text("keep", encoding="utf-8")
        d = self.project("schema_version: 1\n", "tasks: []\n")
        (d / "pmo/views").symlink_to(outside, target_is_directory=True)  # a whole folder
        p = self.render(d)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("inside the project", p.stderr)
        self.assertEqual((outside / "tasks.md").read_text(encoding="utf-8"), "keep")
        (d / "pmo/views").unlink()
        (d / "pmo/views").mkdir()
        (d / "pmo/views/tasks.md").symlink_to(outside / "tasks.md")  # a single view file
        p = self.render(d)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual((outside / "tasks.md").read_text(encoding="utf-8"), "keep")

    def test_paths_into_dot_git_exit_2(self):
        d = self.project("schema_version: 1\npaths: {views: .git}\nregisters: {tasks: {view: config}}\n", "tasks: []\n")
        (d / ".git").mkdir()
        (d / ".git/config").write_text("keep", encoding="utf-8")
        p = self.render(d)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual((d / ".git/config").read_text(encoding="utf-8"), "keep")

    def test_dot_dot_view_exits_2(self):
        d = self.project("schema_version: 1\nregisters: {tasks: {file: tasks.yaml, view: '..'}}\n", "tasks: []\n")
        p = self.render(d)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertNotIn("Traceback", p.stderr)

    def test_register_that_is_not_a_map_is_reported_without_a_traceback(self):
        d = self.project("schema_version: 1\nregisters: {tasks: 5}\n", "tasks: []\n")
        p = self.render(d)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("register `tasks` needs `file`", p.stdout)

    def test_merge_rules(self):
        d = self.project("schema_version: 1\nproject: {name: Acme}\nvocab: {task_status: [a, b], rag: null}\n"
                         "doc_types: {roadmap: null}\n")
        c = pc.load_config(d)
        self.assertEqual(c["project"]["name"], "Acme")
        self.assertEqual(c["project"]["period_format"], "YYYY-MM")  # map merged
        self.assertEqual(c["vocab"]["task_status"], ["a", "b"])  # list replaced
        self.assertNotIn("rag", c["vocab"])  # null removes
        self.assertNotIn("roadmap", c["doc_types"])

    def test_config_that_is_not_a_map_exits_2(self):
        for cfg in ("- a\n- b\n", "schema_version: 1\npaths: null\n", "schema_version: 1\nregisters: [x]\n",
                    "doc_types: null\n", "doc_types: [a]\n", "vocab: null\n", "vocab: text\n"):
            with self.assertRaises(SystemExit) as cm:
                pc.load_config(self.project(cfg))
            self.assertEqual(cm.exception.code, 2, cfg)

    def test_newer_schema_refused(self):
        with self.assertRaises(SystemExit):
            pc.load_config(self.project("schema_version: 99\n"))

    def test_load_config_repeated_key_and_bad_yaml_exit_2(self):
        for cfg in (
            "schema_version: 1\nproject: {name: A}\nproject: {name: B}\n",
            "schema_version: 1\nproject: {name: [\n",
        ):
            d = self.project(cfg)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as cm:
                    pc.load_config(d)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("not valid YAML", err.getvalue())

    def test_schema_version_values(self):
        for bad in (True, 0, -5, '"1"', 1.0):
            d = self.project(f"schema_version: {bad}\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as cm:
                    pc.load_config(d)
            self.assertEqual(cm.exception.code, 2, f"for bad={bad!r}")
            self.assertIn("schema_version must be a whole number of 1 or more", err.getvalue(), f"for bad={bad!r}")

        d2 = self.project("schema_version: 2\n")
        err2 = io.StringIO()
        with contextlib.redirect_stderr(err2):
            with self.assertRaises(SystemExit) as cm2:
                pc.load_config(d2)
        self.assertEqual(cm2.exception.code, 2)
        self.assertIn("newer than this skill knows", err2.getvalue())

        d_ok = self.project("schema_version: 1\n")
        cfg = pc.load_config(d_ok)
        self.assertEqual(cfg["schema_version"], 1)

    def test_missing_register_is_empty(self):
        d = self.project()
        c = pc.load_config(d)
        self.assertEqual(pc.load_register(d, c, "risks"), [])
        self.assertEqual(pc.load_register(d, c, "nope"), [])

    def test_register_and_override_lookup(self):
        d = self.project(register="tasks:\n  - {id: T-1, title: x, due: 2026-01-02}\n")
        c = pc.load_config(d)
        self.assertEqual(pc.load_register(d, c, "tasks")[0]["id"], "T-1")
        self.assertEqual(pc.find_asset(d, c, "templates", "roadmap.md")[1], "skill")
        (d / "pmo/templates").mkdir()
        (d / "pmo/templates/roadmap.md").write_text("x", encoding="utf-8")
        self.assertEqual(pc.find_asset(d, c, "templates", "roadmap.md")[1], "project")

    def test_front_matter_and_type(self):
        self.assertEqual(pc.doc_type("---\ntype: roadmap\n---\nbody"), "roadmap")
        self.assertIsNone(pc.doc_type("no front matter"))
        self.assertEqual(pc.split_front_matter("---\n: [\n---\nb")[0], {})

    def test_non_map_front_matter_and_non_text_type(self):
        self.assertEqual(pc.split_front_matter("---\n- a\n---\nb")[0], {})
        with self.assertRaises(pc.yaml.YAMLError):
            pc.split_front_matter("---\n- a\n---\nb", strict=True)
        self.assertIsNone(pc.doc_type("---\ntype: [x]\n---\nb"))

    def test_to_date_datetime(self):
        import datetime
        self.assertEqual(pc.to_date(datetime.datetime(2026, 1, 2, 3, 4)), datetime.date(2026, 1, 2))

    def test_cell_escapes(self):
        self.assertEqual(pc.cell(["a|b", None, 3]), "a\\|b, , 3")
        self.assertEqual(pc.cell("x\ny"), "x y")
        self.assertEqual(pc.to_date("2026-01-02").day, 2)


class Helpers(unittest.TestCase):
    def test_week_of(self):
        # Monday start (0)
        self.assertEqual(pc.week_of(datetime.date(2026, 11, 6), 0), "2026-W45")
        # Saturday start (5)
        self.assertEqual(pc.week_of(datetime.date(2026, 11, 6), 5), "2026-W45")
        self.assertEqual(pc.week_of(datetime.date(2026, 11, 7), 5), "2026-W46")
        # Sunday start (6)
        self.assertEqual(pc.week_of(datetime.date(2026, 12, 27), 6), "2026-W53")
        # Monday start (0)
        self.assertEqual(pc.week_of(datetime.date(2027, 1, 1), 0), "2026-W53")

    def test_period_range(self):
        # 2026-03 -> (03-01, 03-31)
        self.assertEqual(pc.period_range("2026-03", 0), (datetime.date(2026, 3, 1), datetime.date(2026, 3, 31)))
        # 2026-W46 with Saturday start (5)
        self.assertEqual(pc.period_range("2026-W46", 5), (datetime.date(2026, 11, 7), datetime.date(2026, 11, 13)))
        # 2026-W46 with Monday start (0)
        self.assertEqual(pc.period_range("2026-W46", 0), (datetime.date(2026, 11, 9), datetime.date(2026, 11, 15)))
        # 2025-W53 raises ValueError
        with self.assertRaises(ValueError):
            pc.period_range("2025-W53", 0)
        # 2026-13 raises ValueError
        with self.assertRaises(ValueError):
            pc.period_range("2026-13", 0)

    def test_resolve_period(self):
        as_of = datetime.date(2026, 11, 6)
        # given period wins
        self.assertEqual(pc.resolve_period("2026-04", False, as_of, 0), "2026-04")
        self.assertEqual(pc.resolve_period("2026-W10", False, as_of, 0), "2026-W10")
        # week=True uses week_of
        self.assertEqual(pc.resolve_period(None, True, as_of, 0), "2026-W45")
        # default is the month
        self.assertEqual(pc.resolve_period(None, False, as_of, 0), "2026-11")

    def test_md_table(self):
        # header and separator format, | in cell escaped
        res = pc.md_table(["ID", "Name"], [["T-1", "A|B"]])
        self.assertEqual(res, "| ID | Name |\n|---|---|\n| T-1 | A\\|B |\n")
        # no rows gives | None |  | style row with the right number of cells
        empty_res = pc.md_table(["ID", "Name", "Extra"], [])
        self.assertEqual(empty_res, "| ID | Name | Extra |\n|---|---|---|\n| None |  |  |\n")

    def test_person(self):
        names = {"alice": "Alice Example", "bob": "Bob Sample"}
        # slug -> name
        self.assertEqual(pc.person("alice", names), "Alice Example")
        # list -> joined names
        self.assertEqual(pc.person(["alice", "bob"], names), "Alice Example, Bob Sample")
        # unknown text kept
        self.assertEqual(pc.person("charlie", names), "charlie")
        # None and "" -> not set
        self.assertEqual(pc.person(None, names), "not set")
        self.assertEqual(pc.person("", names), "not set")
        self.assertEqual(pc.person([], names), "not set")

    def test_rag(self):
        acme = Path(__file__).resolve().parents[1] / "examples/acme"
        cfg = pc.load_config(acme)
        tasks = pc.load_register(acme, cfg, "tasks")
        milestones = pc.load_register(acme, cfg, "milestones")
        issues = pc.load_register(acme, cfg, "issues")
        risks = pc.load_register(acme, cfg, "risks")

        # Acme as of 2026-03-15: T-1 (high, due 03-10, in progress) is overdue -> red, reason names T-1
        val, reason = pc.rag(cfg, datetime.date(2026, 3, 15), tasks, milestones, issues, risks)
        self.assertEqual(val, "red")
        self.assertIn("T-1", reason)

        # In-memory amber case: a blocked medium task only
        amber_tasks = [{"id": "T-2", "priority": "medium", "status": "blocked", "due": "2026-04-01"}]
        val, reason = pc.rag(cfg, datetime.date(2026, 3, 15), amber_tasks)
        self.assertEqual(val, "amber")
        self.assertIn("T-2", reason)

        # In-memory green case: nothing open is late
        green_tasks = [{"id": "T-3", "priority": "low", "status": "done", "due": "2026-03-01"}]
        val, reason = pc.rag(cfg, datetime.date(2026, 3, 15), green_tasks)
        self.assertEqual(val, "green")
        self.assertIn("all items on track", reason)

    def test_rag_with_empty_priority_order_has_no_top_priority(self):
        acme = Path(__file__).resolve().parents[1] / "examples/acme"
        cfg = pc.load_config(acme)
        cfg["vocab"]["priority_order"] = []
        val, _ = pc.rag(cfg, datetime.date(2026, 3, 15), [{"id": "T-9", "status": "in-progress", "due": "2026-03-01"}])
        self.assertEqual(val, "amber")

    def test_rag_without_risk_levels_ignores_unrated_risks(self):
        cfg = {"vocab": {"risk_level": []}}
        self.assertEqual(pc.rag(cfg, datetime.date(2026, 3, 15), [], risks=[{"id": "R-1", "status": "open"}]), ("green", "all items on track"))

    def test_week_and_period_helpers_refuse_a_start_outside_0_to_6(self):
        for bad in (-1, 7):
            with self.assertRaises(ValueError):
                pc.week_of(datetime.date(2026, 3, 1), bad)
            with self.assertRaises(ValueError):
                pc.period_range("2026-03", bad)

    def test_every_day_is_inside_its_own_week_for_every_start_day(self):
        day = datetime.date(2024, 12, 1)
        while day < datetime.date(2027, 2, 1):
            for start in range(7):
                first, last = pc.period_range(pc.week_of(day, start), start)
                self.assertTrue(first <= day <= last, (day, start))
                self.assertEqual((last - first).days, 6)
                self.assertEqual(first.weekday(), start)
            day += datetime.timedelta(days=1)

    def test_week_53_exists_only_in_long_years(self):
        self.assertEqual(pc.period_range("2026-W53", 0), (datetime.date(2026, 12, 28), datetime.date(2027, 1, 3)))
        self.assertEqual(pc.week_of(datetime.date(2027, 1, 3), 0), "2026-W53")
        self.assertEqual(pc.week_of(datetime.date(2027, 1, 4), 0), "2027-W01")
        for start in range(7):
            with self.assertRaises(ValueError):
                pc.period_range("2025-W53", start)

    def test_period_range_month_ends(self):
        for period, last in (("2024-02", 29), ("2023-02", 28), ("2100-02", 28), ("2000-02", 29), ("2026-12", 31), ("2026-04", 30)):
            self.assertEqual(pc.period_range(period, 0)[1], datetime.date(int(period[:4]), int(period[5:]), last), period)
        self.assertEqual(pc.period_range("2026-01", 0)[0], datetime.date(2026, 1, 1))

    def test_period_range_and_resolve_period_refuse_malformed_periods(self):
        for bad in ("", "2026", "2026-1", "2026-00", "2026-13", "2026-W00", "2026-W54", "2026-w10", "2026-03-01", " 2026-03", "2026-03\n", "٢٠٢٦-٠٣", "٢٠٢٦-03", "٢٠٢٦-W10"):
            with self.subTest(period=bad):
                with self.assertRaises(ValueError):
                    pc.period_range(bad, 0)
                if bad:  # an empty period means "none given"
                    with self.assertRaises(ValueError):
                        pc.resolve_period(bad, False, datetime.date(2026, 3, 1), 0)

    def test_resolve_period_week_follows_the_start_day(self):
        sat = datetime.date(2026, 11, 7)
        self.assertEqual(pc.resolve_period(None, True, sat, 0), "2026-W45")
        self.assertEqual(pc.resolve_period(None, True, sat, 5), "2026-W46")
        self.assertEqual(pc.resolve_period("", False, sat, 0), "2026-11")  # empty counts as not given
        self.assertEqual(pc.resolve_period(None, False, datetime.date(2024, 2, 29), 0), "2024-02")

    def test_week_start_values(self):
        self.assertEqual(pc.week_start({}), 0)
        self.assertEqual(pc.week_start({"project": None}), 0)
        self.assertEqual(pc.week_start({"project": {"week_start": None}}), 0)
        self.assertEqual(pc.week_start({"project": {"week_start": "SUNDAY"}}), 6)
        for bad in (5, "someday", ""):
            with self.assertRaises(ValueError):
                pc.week_start({"project": {"week_start": bad}})

    def test_person_edge_values(self):
        self.assertEqual(pc.person(7, {"7": "Seven"}), "Seven")
        self.assertEqual(pc.person(7, {}), "7")
        self.assertEqual(pc.person("   ", {}), "not set")
        self.assertEqual(pc.person([None, ""], {}), "not set")
        self.assertEqual(pc.person([1, "a", None], {"a": "A"}), "1, A")

    def test_md_table_cells(self):
        t = pc.md_table(["A", "B"], [[None, True], [["x", "y|z"], {"k": "v"}], ["line\nbreak", datetime.date(2026, 1, 2)], ["مرحبا", "é"]])
        self.assertEqual(t.splitlines()[2:], ["|  | True |", "| x, y\\|z | k: v |", "| line break | 2026-01-02 |", "| مرحبا | é |"])
        self.assertTrue(t.endswith("\n"))

    def test_statuses_shapes(self):
        self.assertEqual(pc.statuses({"registers": {"tasks": {"closed": "done"}}}, "tasks", "closed"), ["done"])
        self.assertEqual(pc.statuses({"registers": {"tasks": {"closed": [1, 2]}}}, "tasks", "closed"), [1, 2])
        self.assertEqual(pc.statuses({"registers": {"tasks": {"closed": None}}}, "tasks", "closed"), [])
        self.assertEqual(pc.statuses({"registers": {"tasks": "x"}}, "tasks", "closed"), [])
        self.assertEqual(pc.statuses({"registers": []}, "tasks", "closed"), [])

    def test_front_matter_edges(self):
        self.assertEqual(pc.split_front_matter("---\n\n---\nbody"), ({}, "body"))
        self.assertEqual(pc.split_front_matter("---\ntype: x\n---\n"), ({"type": "x"}, ""))
        self.assertEqual(pc.split_front_matter("no front matter\n---\na: 1\n---\n"), (None, "no front matter\n---\na: 1\n---\n"))
        fm, body = pc.split_front_matter("---\na: [\n---\nbody\n")
        self.assertEqual((fm, body), ({}, "body\n"))
        with self.assertRaises(Exception):
            pc.split_front_matter("---\na: [\n---\nbody\n", strict=True)
        with self.assertRaises(Exception):
            pc.split_front_matter("---\n- a\n---\n", strict=True)

    def test_rag_rules_each_fire_with_their_reason(self):
        cfg = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        top = cfg["vocab"]["priority_order"][0]
        d = datetime.date(2026, 3, 15)
        t = lambda i, **kw: {"id": i, "priority": "low", "status": "todo", **kw}  # noqa: E731
        # red: a top-priority task that is blocked (not overdue)
        self.assertEqual(pc.rag(cfg, d, [t("T-1", priority=top, status="blocked")]), ("red", "top-priority task T-1 is blocked"))
        # red: several top-priority tasks overdue -> plural
        self.assertEqual(pc.rag(cfg, d, [t("T-1", priority=top, due="2026-03-01"), t("T-2", priority=top, due="2026-03-02")])[1], "top-priority tasks T-1, T-2 are overdue")
        # a closed top-priority task counts for nothing
        self.assertEqual(pc.rag(cfg, d, [t("T-1", priority=top, status="done", due="2026-03-01")])[0], "green")
        # red: an overdue milestone
        self.assertEqual(pc.rag(cfg, d, [], [{"id": "M-1", "status": "open", "due": "2026-03-14"}]), ("red", "milestone M-1 is overdue"))
        # a closed milestone is not overdue
        closed = cfg["registers"]["milestones"]["closed"][0]
        self.assertEqual(pc.rag(cfg, d, [], [{"id": "M-1", "status": closed, "due": "2026-03-14"}])[0], "green")
        # red: three late tasks, reason lists three ids at most
        late = [t(f"T-{n}", due="2026-03-01") for n in range(1, 6)]
        self.assertEqual(pc.rag(cfg, d, late), ("red", "3 or more tasks are blocked or overdue (T-1, T-2, T-3)"))
        # amber: two late tasks, a task due today is not overdue
        self.assertEqual(pc.rag(cfg, d, late[:2])[1], "tasks T-1, T-2 are overdue")
        self.assertEqual(pc.rag(cfg, d, [t("T-1", due="2026-03-15")])[0], "green")
        self.assertEqual(pc.rag(cfg, d, [t("T-1", due="2026-03-14")])[0], "amber")

    def test_rag_issue_severity_and_risk_impact_rules(self):
        cfg = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        d = datetime.date(2026, 3, 15)
        sev = cfg["vocab"]["issue_severity"]
        impact = cfg["vocab"]["risk_level"][-1]
        closed_issue = cfg["registers"]["issues"]["closed"][0]
        closed_risk = cfg["registers"]["risks"]["closed"][0]
        self.assertEqual(pc.rag(cfg, d, [], issues=[{"id": "I-1", "status": "open", "severity": sev[-1]}]), ("amber", "open issue I-1 has high severity"))
        self.assertEqual(pc.rag(cfg, d, [], issues=[{"id": "I-1", "status": "open", "severity": sev[-2]}])[0], "amber")
        self.assertEqual(pc.rag(cfg, d, [], issues=[{"id": "I-1", "status": "open", "severity": sev[0]}])[0], "green")
        self.assertEqual(pc.rag(cfg, d, [], issues=[{"id": "I-1", "status": closed_issue, "severity": sev[-1]}])[0], "green")
        self.assertEqual(pc.rag(cfg, d, [], risks=[{"id": "R-1", "status": "open", "impact": impact}, {"id": "R-2", "status": "open", "impact": impact}]),
                         ("amber", "open risks R-1, R-2 have high impact"))
        self.assertEqual(pc.rag(cfg, d, [], risks=[{"id": "R-1", "status": closed_risk, "impact": impact}])[0], "green")

    def test_rag_milestone_due_within_seven_days_boundaries(self):
        cfg = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        d = datetime.date(2026, 3, 15)
        for due, want in (("2026-03-15", "amber"), ("2026-03-22", "amber"), ("2026-03-23", "green"), ("2026-03-14", "red")):
            with self.subTest(due=due):
                self.assertEqual(pc.rag(cfg, d, [], [{"id": "M-1", "status": "open", "due": due}])[0], want)
        self.assertEqual(pc.rag(cfg, d, [], [{"id": "M-1", "status": "open", "due": "2026-03-20"}])[1], "milestone M-1 is due within 7 days")
        # a milestone with an unreadable or missing date is ignored
        for due in ("not a date", None, 5):
            self.assertEqual(pc.rag(cfg, d, [], [{"id": "M-1", "status": "open", "due": due}])[0], "green")

    def test_rag_with_a_short_or_custom_vocabulary(self):
        base = {"registers": {"tasks": {"closed": ["done"], "blocked": ["blocked"]}}, "vocab": {"priority_order": ["p1"]}}
        d = datetime.date(2026, 3, 15)
        red = [{"id": "T-1", "priority": "p1", "status": "blocked"}]
        for rag_vocab, want in ((["G"], "red"), (["G", "A"], "red"), (["G", "A", "R"], "R"), (None, "red")):
            cfg = {**base, "vocab": {**base["vocab"], **({"rag": rag_vocab} if rag_vocab else {})}}
            self.assertEqual(pc.rag(cfg, d, red)[0], want if want != "red" else "red")
        amber = [{"id": "T-1", "priority": "p2", "status": "blocked"}]
        self.assertEqual(pc.rag({**base, "vocab": {**base["vocab"], "rag": ["G"]}}, d, amber)[0], "amber")
        self.assertEqual(pc.rag({**base, "vocab": {**base["vocab"], "rag": ["G", "A", "R"]}}, d, amber)[0], "A")
        self.assertEqual(pc.rag({**base, "vocab": {**base["vocab"], "rag": ["G", "A", "R"]}}, d, [])[0], "G")

    def test_glossary_paths_shapes(self):
        gp = lambda g, lang="xx": pc.glossary_paths({"languages": {"xx": {"glossary": g}}}, lang)  # noqa: E731
        self.assertEqual(gp("a/b/g.txt"), ("a/b/g.txt", "a/b/g.proposed.txt"))
        self.assertEqual(gp("g.txt"), ("g.txt", "g.proposed.txt"))
        self.assertEqual(gp("g"), ("g", "g.proposed"))
        for bad in (None, 5, "  ", ["a"]):
            self.assertEqual(gp(bad), (None, None))
        self.assertEqual(gp("g.md", "yy"), (None, None))
        self.assertEqual(pc.glossary_paths({"languages": {"xx": "s"}}, "xx"), (None, None))
        self.assertEqual(pc.glossary_paths({"languages": [1]}, "xx"), (None, None))
        self.assertEqual(pc.glossary_paths([], "xx"), (None, None))

    def test_languages_shapes(self):
        self.assertEqual(pc.languages({"languages": "x"}), {"draft": "en", "translations": [], "info": {"en": {}}})
        self.assertEqual(pc.languages(None)["draft"], "en")
        got = pc.languages({"languages": {"draft": "", "translations": ["xx", 5, "yy"], "xx": {"dir": "rtl"}, "yy": "bad"}})
        self.assertEqual(got, {"draft": "en", "translations": ["xx", "yy"], "info": {"en": {}, "xx": {"dir": "rtl"}, "yy": {}}})
        self.assertEqual(pc.languages({"languages": {"draft": "fr", "translations": "xx"}})["translations"], [])

    def test_config_errors_reports_week_start(self):
        import render_views
        cfg = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        cfg["project"]["week_start"] = "someday"
        errs = render_views.config_errors(cfg)
        self.assertTrue(any("week_start" in e and "someday" in e for e in errs))

    def test_read_strips_a_bom(self):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write(chr(0xFEFF) + "---\ntype: x\n---\nbody\n")
            path = f.name
        try:
            text = pc.read(path)
            self.assertTrue(text.startswith("---"))
        finally:
            Path(path).unlink(missing_ok=True)

    def test_front_matter_edge_forms(self):
        fm1, b1 = pc.split_front_matter("---\n---\nbody\n")
        self.assertEqual(fm1, {})
        self.assertEqual(b1, "body\n")

        fm2, b2 = pc.split_front_matter("---\ntype: x\n---")
        self.assertEqual(fm2, {"type": "x"})
        self.assertEqual(b2, "")

        fm3, b3 = pc.split_front_matter("---\ntype: x\n--- \nbody\n")
        self.assertEqual(fm3, {"type": "x"})
        self.assertEqual(b3, "body\n")

        fm4, b4 = pc.split_front_matter("type: x\n---\n")
        self.assertIsNone(fm4)
        self.assertEqual(b4, "type: x\n---\n")

        fm5, b5 = pc.split_front_matter("---\nnote: a---\ntype: x\n---\n")
        self.assertEqual(fm5, {"note": "a---", "type": "x"})

    def test_front_matter_impossible_date(self):
        fm, body = pc.split_front_matter("---\ntype: x\nlast_updated: 2026-02-30\n---\nbody\n")
        self.assertEqual((fm, body), ({}, "body\n"))
        with self.assertRaises(pc.yaml.YAMLError):
            pc.split_front_matter("---\ntype: x\nlast_updated: 2026-02-30\n---\nbody\n", strict=True)

    def test_load_yaml_refuses_a_repeated_key(self):
        with self.assertRaises(pc.yaml.YAMLError):
            pc.load_yaml("a: 1\na: 2\n")
        with self.assertRaises(pc.yaml.YAMLError):
            pc.load_yaml("risks:\n- {id: R-1, status: open, status: closed}\n")
        self.assertEqual(pc.load_yaml("a: [1, 2]\nb: {c: 1}\n"), {"a": [1, 2], "b": {"c": 1}})
        self.assertIsNone(pc.load_yaml(""))

    def test_load_yaml_refuses_aliases_quickly(self):
        lines = ["a0: &a0 " + str(["x"] * 9)]
        for i in range(1, 8):
            lines.append(f"a{i}: &a{i} " + "[" + ", ".join([f"*a{i-1}"] * 9) + "]")
        lines.append("title: *a7\n")
        nested_alias_text = "\n".join(lines)

        t0 = time.monotonic()
        with self.assertRaises(pc.yaml.YAMLError):
            pc.load_yaml(nested_alias_text)
        elapsed = time.monotonic() - t0
        self.assertLess(elapsed, 5.0)

        with self.assertRaises(pc.yaml.YAMLError):
            pc.load_yaml("a: &x 1\nb: *x\n")

        with self.assertRaises(pc.yaml.YAMLError):
            pc.load_yaml("a: &x 1\n")

        with self.assertRaises(pc.yaml.YAMLError) as cm:
            pc.load_yaml("a: {x: 1, <<: {y: 2}}\n")
        self.assertIn("merge keys", str(cm.exception))

    def test_to_date_strict(self):
        with self.assertRaises(ValueError):
            pc.to_date("20260301")
        with self.assertRaises(ValueError):
            pc.to_date(20260301)
        with self.assertRaises(ValueError):
            pc.to_date("2026-W10-1")
        self.assertEqual(pc.to_date("2026-03-01"), datetime.date(2026, 3, 1))
        d = datetime.date(2026, 3, 1)
        self.assertEqual(pc.to_date(d), d)
        dt = datetime.datetime(2026, 3, 1, 10, 30)
        self.assertEqual(pc.to_date(dt), d)
        self.assertIsNone(pc.to_date(None))
        self.assertIsNone(pc.to_date(""))

    def test_cell_backslashes_and_carriage_return(self):
        self.assertEqual(pc.cell("a\\|b"), r"a\\\|b")
        self.assertEqual(pc.cell("a|b"), r"a\|b")
        self.assertEqual(pc.cell("x\\"), "x\\")
        self.assertEqual(pc.cell(r"C:\Users"), r"C:\Users")
        self.assertEqual(pc.cell("p\rq"), "p q")
        self.assertEqual(pc.cell("p\r\nq"), "p q")
        tbl = pc.md_table(["a", "b"], [["a\\|b", "y"]])
        lines = tbl.splitlines()
        self.assertEqual(lines[2], r"| a\\\|b | y |")


class Languages(unittest.TestCase):
    def test_missing_block_is_english_only(self):
        c = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        info = pc.languages(c)
        self.assertEqual(info["draft"], "en")
        self.assertEqual(info["translations"], [])
        self.assertEqual(info["info"]["en"]["dir"], "ltr")

    def test_project_block_merges(self):
        base = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        merged = pc.merge(base, {
            "languages": {
                "translations": ["xx"],
                "xx": {"label": "XX", "dir": "rtl"}
            }
        })
        info = pc.languages(merged)
        self.assertEqual(info["info"]["xx"]["dir"], "rtl")

    def test_type_translations_and_flag(self):
        base = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        merged = pc.merge(base, {
            "languages": {
                "translations": ["xx"],
                "xx": {"label": "XX", "dir": "rtl"}
            }
        })
        self.assertEqual(pc.type_translations(merged, "status-report"), ["xx"])
        overridden = pc.merge(merged, {
            "doc_types": {
                "status-report": {"translations": []}
            }
        })
        self.assertEqual(pc.type_translations(overridden, "status-report"), [])
        self.assertEqual(pc.type_translations(merged, "docs-audit-report"), [])
        self.assertEqual(pc.type_translations(merged, "overdue-report"), [])
        self.assertEqual(pc.translate_flag(merged, "status-report"), "in-period")
        with_flag = pc.merge(merged, {
            "doc_types": {
                "status-report": {"translate": "after-close"}
            }
        })
        self.assertEqual(pc.translate_flag(with_flag, "status-report"), "after-close")

    def test_translation_rel(self):
        self.assertEqual(
            pc.translation_rel("pmo/documents/2026-03 - Status report.md", "xx"),
            "pmo/documents/2026-03 - Status report.xx.md"
        )
        with self.assertRaises(ValueError):
            pc.translation_rel("notes.txt", "xx")

    def test_body_hash_ignores_front_matter_comments_and_blank_lines(self):
        draft = (
            "---\n"
            "status: draft\n"
            "---\n"
            "<!-- draft comment -->\n"
            "\n"
            "# Title\n"
            "\n"
            "Paragraph text.  \n"
            "<!-- another comment -->\n"
        )
        finished = (
            "---\n"
            "status: finished\n"
            "source_hashes:\n"
            "  tasks: 12345678\n"
            "---\n"
            "# Title\n"
            "Paragraph text.\n"
        )
        h1 = pc.body_hash(draft)
        h2 = pc.body_hash(finished)
        self.assertEqual(len(h1), 8)
        self.assertEqual(h1, h2)
        different = finished + "\nExtra word.\n"
        self.assertNotEqual(h1, pc.body_hash(different))

    def test_glossary_paths(self):
        base = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        cfg = pc.merge(base, {
            "languages": {
                "xx": {"glossary": "pmo/data/glossary-xx.md"}
            }
        })
        approved, proposed = pc.glossary_paths(cfg, "xx")
        self.assertEqual(approved, "pmo/data/glossary-xx.md")
        self.assertEqual(proposed, "pmo/data/glossary-xx.proposed.md")
        self.assertEqual(pc.glossary_paths(base, "en"), (None, None))

    def test_languages_drops_repeats_and_bad_codes(self):
        got1 = pc.languages({"languages": {"draft": "en", "translations": ["ar", "ar", "en"]}})
        self.assertEqual(got1["translations"], ["ar"])

        got2 = pc.languages({"languages": {"draft": "en", "translations": ["/../../../x", "AR", "fr-CA", 5]}})
        self.assertEqual(got2["translations"], ["fr-CA"])
        self.assertEqual(sorted(got2["info"].keys()), ["en", "fr-CA"])

    def test_run_turns_an_exception_into_exit_2(self):
        err = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"PMO_DEBUG": ""}):
            with contextlib.redirect_stderr(err):
                self.assertEqual(pc.run(lambda: 1 / 0), 2)
        self.assertIn("ZeroDivisionError", err.getvalue())
        self.assertEqual(pc.run(lambda: 0), 0)
        self.assertEqual(pc.run(lambda: 1), 1)

        def boom():
            raise SystemExit(3)

        with self.assertRaises(SystemExit) as cm:
            pc.run(boom)
        self.assertEqual(cm.exception.code, 3)
        with unittest.mock.patch.dict(os.environ, {"PMO_DEBUG": "1"}):
            with self.assertRaises(ZeroDivisionError):
                pc.run(lambda: 1 / 0)

    def test_id_num(self):
        self.assertEqual(pc.id_num("R-10"), 10)
        self.assertEqual(pc.id_num("none"), 0)


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"
TOOLS = ["docs_audit.py", "generate.py", "overdue.py", "parity_check.py", "render_views.py", "setup.py", "structure_check.py", "where.py"]


class EveryTool(unittest.TestCase):
    def run_tool(self, name, *args):
        p = subprocess.run([sys.executable, str(SCRIPTS / name), *args], capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout + p.stderr

    def test_every_tool_answers_help(self):
        for name in TOOLS + ["renumber.py", "publish.py"]:
            code, out = self.run_tool(name, "--help")
            self.assertEqual(code, 0, name)
            self.assertIn("usage", out.lower(), name)
            self.assertIn("Exit codes", out, name)

    def test_newer_schema_is_refused_and_nothing_is_written(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        (d / "pmo").mkdir()
        (d / "pmo/config.yaml").write_text("schema_version: 99\n", encoding="utf-8")
        for name in ["docs_audit.py", "overdue.py", "render_views.py", "structure_check.py"]:
            code, out = self.run_tool(name, "--project", str(d))
            self.assertEqual(code, 2, f"{name}: {out}")
            self.assertIn("schema_version", out, name)
        self.assertEqual(sorted(p.name for p in (d / "pmo").iterdir()), ["config.yaml"])

    def test_no_tool_stages_or_commits(self):
        verbs = r"(add|commit|push|restore|rm|reset|checkout|stash|clean)"
        git_literal = re.compile(r"""["']git["']""")
        verb_literal = re.compile(r"""["']""" + verbs + r"""["']""")
        git_words = re.compile(r"\bgit " + verbs + r"\b")

        # shortcut: textual check, one line at a time; read-only git (rev-parse) is allowed, any writing verb is not
        def bad_lines(text):
            return [ln for ln in text.splitlines()
                    if git_words.search(ln) or (git_literal.search(ln) and verb_literal.search(ln))]

        # the check must flag the calls it is there for, or it proves nothing
        for sample in ('subprocess.run(["git", "-C", str(target_dir), "add", "--", str(t)])',
                       "subprocess.run(['git', 'commit', '-m', 'x'])",
                       'os.system("git push")'):
            self.assertTrue(bad_lines(sample), sample)
        self.assertFalse(bad_lines('subprocess.run(["git", "-C", str(d), "rev-parse", "--show-toplevel"])'))

        for f in SCRIPTS.glob("*.py"):
            self.assertEqual(bad_lines(f.read_text(encoding="utf-8")), [], f.name)


class ConfigGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.root = self.tmp / "acme"
        shutil.copytree(Path(__file__).resolve().parents[1] / "examples/acme", self.root)
        self.cfg_file = self.root / "pmo/config.yaml"

    def cfg_run(self, text, append=True):
        if append:
            with open(self.cfg_file, "a", encoding="utf-8") as f:
                f.write(text)
        else:
            self.cfg_file.write_text(text, encoding="utf-8")
        p = subprocess.run(
            [sys.executable, str(pc.SKILL / "scripts/render_views.py"), "--check", "--project", str(self.root)],
            capture_output=True, text=True, encoding="utf-8"
        )
        return p.returncode, p.stdout, p.stderr

    def test_bad_yaml_exits_2(self):
        code, stdout, stderr = self.cfg_run("project: [unclosed", append=False)
        self.assertEqual(code, 2)
        self.assertIn(str(self.cfg_file), stderr)
        self.assertIn("not valid YAML", stderr)
        self.assertNotIn("Traceback", stderr)
        with self.assertRaises(SystemExit) as cm:
            pc.load_config(self.root)
        self.assertEqual(cm.exception.code, 2)

    def test_non_utf8_config_exits_2(self):
        self.cfg_file.write_bytes(b"project: caf\xe9\n")
        with self.assertRaises(SystemExit) as cm:
            pc.load_config(self.root)
        self.assertEqual(cm.exception.code, 2)
        p = subprocess.run(
            [sys.executable, str(pc.SKILL / "scripts/render_views.py"), "--check", "--project", str(self.root)],
            capture_output=True, text=True, encoding="utf-8"
        )
        self.assertEqual(p.returncode, 2)
        self.assertIn("not valid UTF-8", p.stderr)
        self.assertNotIn("Traceback", p.stderr)

    def test_missing_config_exits_2(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        p = subprocess.run(
            [sys.executable, str(pc.SKILL / "scripts/render_views.py"), "--check", "--project", str(empty)],
            capture_output=True, text=True, encoding="utf-8"
        )
        self.assertEqual(p.returncode, 2)
        self.assertIn("no pmo/config.yaml here", p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        import io
        from unittest.mock import patch
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                pc.load_config(empty)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("no pmo/config.yaml here", mock_stderr.getvalue())
        defaults = pc.load_config(empty, must_exist=False)
        self.assertEqual(defaults["schema_version"], 1)

    def test_bad_values_exit_2(self):
        cases = [
            ("registers: {tasks: {fields: 5}}\n", "registers.tasks.fields", True),
            ("registers: {tasks: {prefix: 5}}\n", "registers.tasks.prefix", True),
            ("registers: {tasks: {enums: [a]}}\n", "registers.tasks.enums", True),
            ("registers: {tasks: {dates: 7}}\n", "registers.tasks.dates", True),
            ("registers: {tasks: {closed: 5}}\n", "registers.tasks.closed", True),
            ("vocab: {task_status: 5}\n", "vocab.task_status", True),
            ("project: just text\n", "project", True),
            ("doc_types: {decision-log: {name: 5}}\n", "doc_types.decision-log.name", True),
            ("doc_types: {decision-log: {stale_days: '30'}}\n", "doc_types.decision-log.stale_days", True),
            ("paths: {templates: null}\n", "paths.templates is missing", False),
        ]
        acme_text = (Path(__file__).resolve().parents[1] / "examples/acme/pmo/config.yaml").read_text(encoding="utf-8")
        for text, key, is_type_error in cases:
            with self.subTest(snippet=text.strip()):
                base = re.sub(r"^project:\n(?:[ \t].*\n)*", "", acme_text, flags=re.M) if text.startswith("project:") else acme_text
                code, stdout, stderr = self.cfg_run(base + "\n" + text, append=False)
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", stderr)
                self.assertIn(key, stderr)
                if is_type_error:
                    self.assertIn("ERROR config:", stderr)

    def test_doc_type_name_outside_project_is_refused(self):
        acme_text = (Path(__file__).resolve().parents[1] / "examples/acme/pmo/config.yaml").read_text(encoding="utf-8")
        code, stdout, stderr = self.cfg_run(acme_text + '\ndoc_types: {decision-log: {name: "../../../escaped-{title}.md"}}\n', append=False)
        self.assertEqual(code, 2)
        self.assertIn("doc_types.decision-log.name", stderr)
        self.assertNotIn("Traceback", stderr)
        with self.assertRaises(SystemExit) as cm:
            pc.load_config(self.root)
        self.assertEqual(cm.exception.code, 2)

    def test_safe_write_refuses_a_symlink_out(self):
        outside_file = self.tmp / "outside.md"
        outside_file.write_text("keep", encoding="utf-8")
        link = self.root / "pmo/views/out.md"
        link.symlink_to(outside_file)
        with self.assertRaises(SystemExit) as cm:
            pc.safe_write(self.root, "pmo/views/out.md", "x")
        self.assertEqual(cm.exception.code, 2)
        self.assertEqual(outside_file.read_text(encoding="utf-8"), "keep")
        pc.safe_write(self.root, "pmo/views/new.md", "hello")
        self.assertEqual((self.root / "pmo/views/new.md").read_text(encoding="utf-8"), "hello")

    def test_register_wrong_top_key(self):
        cfg = pc.load_config(self.root)
        risks_file = self.root / "pmo/registers/risks.yaml"
        risks_file.write_text("risk:\n  - id: R-1\n", encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            pc.load_register(self.root, cfg, "risks")
        self.assertIn("top key must be risks:", str(cm.exception))

        risks_file.write_text("", encoding="utf-8")
        self.assertEqual(pc.load_register(self.root, cfg, "risks"), [])

        risks_file.write_text("risks: []\n", encoding="utf-8")
        self.assertEqual(pc.load_register(self.root, cfg, "risks"), [])

    def test_roster_names_survives_a_wrong_top_key(self):
        cfg = pc.load_config(self.root)
        roster_file = self.root / "pmo/registers/roster.yaml"
        roster_file.write_text("team:\n  - slug: alice\n    name: Alice\n", encoding="utf-8")
        self.assertEqual(pc.roster_names(self.root, cfg), {})


if __name__ == "__main__":
    unittest.main()
