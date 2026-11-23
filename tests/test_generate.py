"""Tests for scripts/generate.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_generate"""
import re
import shutil
import subprocess
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.dont_write_bytecode = True  # importing the shipped scripts must leave no __pycache__
sys.path.insert(0, str(SCRIPTS))
import generate  # noqa: E402
import pmo_common as pc  # noqa: E402
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # child scripts must leave no __pycache__ either


def tool(name, project, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / name), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class TestGenerate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_help(self):
        code, out, _ = tool("generate.py", self.root, "--help")
        self.assertEqual(code, 0)
        self.assertIn("usage", out.lower())

    def test_unknown_type_exits_2(self):
        code, _, err = tool("generate.py", self.root, "no-such-type")
        self.assertEqual(code, 2)
        self.assertIn("unknown doc type", err)

    def test_type_without_generator_exits_2(self):
        code, _, err = tool("generate.py", self.root, "roadmap")
        self.assertEqual(code, 2)
        self.assertIn("no generator configured", err)
        self.assertIn("references/draft.md", err)
        self.assertNotIn("generator: true", err)

    def test_subproject_names_the_file_and_filters_entries(self):
        sys.path.insert(0, str(REPO / "tests"))
        from test_where import make_per_subproject
        make_per_subproject(self.root)
        self.assertEqual(tool("generate.py", self.root, "decision-log")[0], 2)  # per_subproject needs the flag
        self.assertEqual(tool("generate.py", self.root, "decision-log", "--subproject", "ios")[0], 2)
        code, out, _ = tool("generate.py", self.root, "decision-log", "--subproject", "api", "--stdout")
        self.assertEqual(code, 0)
        self.assertIn("DEC-1", out)
        self.assertNotIn("DEC-2", out)
        code, out, _ = tool("generate.py", self.root, "decision-log", "--subproject", "web")
        self.assertEqual((code, out.strip()), (0, "wrote pmo/documents/web - Decision log.md"))

    def test_decision_log_on_acme(self):
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()
        code, out, err = tool("generate.py", self.root, "decision-log", "--as-of", "2026-03-15")
        self.assertEqual(code, 0, err)
        self.assertTrue(doc.exists())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("### DEC-1 - Use weekly releases", text)
        self.assertIn("### DEC-2 - Host on shared cloud", text)
        self.assertIn("Sam Example", text)
        self.assertNotIn("decided_by: sam", text)
        # Check summary table has 2 rows
        lines = [ln for ln in text.split("## Decisions")[0].split("## Summary")[1].splitlines() if ln.startswith("| `DEC-")]
        self.assertEqual(len(lines), 2)
        # Front matter
        self.assertIn("status: draft", text)
        self.assertIn("checks:", text)

    def test_decision_log_passes_its_checks(self):
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()
        code, _, _ = tool("generate.py", self.root, "decision-log", "--as-of", "2026-03-15")
        self.assertEqual(code, 0)
        import structure_check
        cfg = pc.load_config(self.root)
        text = doc.read_text(encoding="utf-8")
        errs, warns = structure_check.check(self.root, cfg, text)
        self.assertEqual(errs, [])
        self.assertNotIn("{{", text)

    def test_refuses_existing_document_exits_3(self):
        doc = self.root / "pmo/documents/Decision log.md"
        before = doc.read_bytes()
        code, out, err = tool("generate.py", self.root, "decision-log")
        self.assertEqual(code, 3)
        self.assertIn("already exists", err)
        self.assertEqual(doc.read_bytes(), before)

    def test_stdout_writes_nothing(self):
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()
        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout", "--as-of", "2026-03-15")
        self.assertEqual(code, 0, err)
        self.assertFalse(doc.exists())
        self.assertIn("# Decision log", out)

    def test_deterministic(self):
        code1, out1, _ = tool("generate.py", self.root, "decision-log", "--stdout", "--as-of", "2026-03-15")
        code2, out2, _ = tool("generate.py", self.root, "decision-log", "--stdout", "--as-of", "2026-03-15")
        self.assertEqual(code1, 0)
        self.assertEqual(code2, 0)
        self.assertEqual(out1, out2)

    def test_generated_draft_records_source_hashes(self):
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()

        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout", "--as-of", "2026-03-15")
        self.assertEqual(code, 0, err)
        w_code, w_out, w_err = tool("where.py", self.root, "decision-log", "--hashes")
        self.assertEqual(w_code, 0, w_err)
        where_sh = [line for line in w_out.splitlines() if line.startswith("source_hashes:")][0]
        fm_lines = [line for line in out.split("---")[1].splitlines() if line.startswith("source_hashes:")]
        self.assertEqual(len(fm_lines), 1)
        self.assertEqual(fm_lines[0], where_sh)

        code, out, err = tool("generate.py", self.root, "decision-log", "--as-of", "2026-03-15")
        self.assertEqual(code, 0, err)
        self.assertTrue(doc.exists())
        clean_text = re.sub(r"<!--.*?-->\n*", "", doc.read_text(encoding="utf-8")).replace("- {{question}}", "- None")
        doc.write_text(clean_text, encoding="utf-8")
        sc_code, sc_out, sc_err = tool("structure_check.py", self.root, str(doc))
        self.assertEqual(sc_code, 0, sc_out + sc_err)

        if doc.exists():
            doc.unlink()
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\ndoc_types:\n  decision-log:\n    generated_from: []\n", encoding="utf-8")
        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout", "--as-of", "2026-03-15")
        self.assertEqual(code, 0, err)
        fm, _ = pc.split_front_matter(out, strict=True)
        self.assertNotIn("source_hashes", fm)
        self.assertFalse(any(line.startswith("source_hashes:") for line in out.split("---")[1].splitlines()))

    def test_invalid_register_exits_1_and_writes_nothing(self):
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()
        dec_file = self.root / "pmo/registers/decisions.yaml"
        dec_file.write_text("decisions:\n  - {id: DEC-1, title: a}\n  - {id: DEC-1, title: b}\n", encoding="utf-8")
        code, out, err = tool("generate.py", self.root, "decision-log")
        self.assertEqual(code, 1)
        self.assertIn("duplicate id", err)
        self.assertFalse(doc.exists())

    def test_missing_section_exits_2(self):
        tpl_dir = self.root / "pmo/templates"
        tpl_dir.mkdir(parents=True, exist_ok=True)
        orig = (REPO / "skills/pmo-docs/assets/templates/decision-log.md").read_text(encoding="utf-8")
        modified = orig.replace("## Summary", "## Overview")
        (tpl_dir / "decision-log.md").write_text(modified, encoding="utf-8")
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()
        code, out, err = tool("generate.py", self.root, "decision-log")
        self.assertEqual(code, 2)
        self.assertIn("Summary", err)
        self.assertIn("generator: null", err)

    def test_missing_slot_exits_2(self):
        tpl_dir = self.root / "pmo/templates"
        tpl_dir.mkdir(parents=True, exist_ok=True)
        orig = (REPO / "skills/pmo-docs/assets/templates/team-checklist.md").read_text(encoding="utf-8")
        modified = orig.replace("## {{team}} - {{lead}}", "## Teams")
        (tpl_dir / "team-checklist.md").write_text(modified, encoding="utf-8")
        code, _, err = tool("generate.py", self.root, "team-checklist", "2026-03", "--stdout")
        self.assertEqual(code, 2)
        self.assertIn("template missing section `{{team}} - {{lead}}`", err)
        self.assertIn("generator: null", err)

    def test_generator_null_in_project_config_exits_2(self):
        cfg_file = self.root / "pmo/config.yaml"
        cfg_text = cfg_file.read_text(encoding="utf-8")
        cfg_file.write_text(cfg_text + "\ndoc_types:\n  decision-log:\n    generator: null\n", encoding="utf-8")
        code, out, err = tool("generate.py", self.root, "decision-log")
        self.assertEqual(code, 2)
        self.assertIn("no generator configured", err)

    def test_team_checklist_on_acme(self):
        # Add a task with unknown team in temp copy
        tasks_file = self.root / "pmo/registers/tasks.yaml"
        tasks_text = tasks_file.read_text(encoding="utf-8")
        tasks_file.write_text(tasks_text + "  - {id: T-99, title: Orphan task, team: unknown, status: not-started, due: 2026-03-20, period: 2026-03}\n", encoding="utf-8")

        code, out, err = tool("generate.py", self.root, "team-checklist", "2026-03", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)

        # Team blocks in team order
        self.assertIn("## Platform - Alice Example", out)
        self.assertIn("## Web - Bob Example", out)
        self.assertLess(out.index("## Platform - Alice Example"), out.index("## Web - Bob Example"))

        # Groups under Platform
        self.assertIn("**docs**", out)
        self.assertIn("**infra**", out)

        # T-3 line starts with - [x]
        self.assertTrue(re.search(r"-\s*\[x\].*`T-3`", out))

        # Check unknown team appears under ## No team - not set
        self.assertIn("## No team - not set", out)
        self.assertGreater(out.index("`T-99`"), out.index("## No team - not set"))

        # Verify progress counts match Acme's march tasks from register
        cfg = pc.load_config(self.root)
        march_tasks = [t for t in pc.load_register(self.root, cfg, "tasks") if t.get("period") == "2026-03"]
        task_closed = pc.statuses(cfg, "tasks", "closed")
        done = sum(1 for t in march_tasks if t.get("status") in task_closed)
        total = len(march_tasks)
        pct = round(100 * done / total)
        self.assertIn(f"**Progress:** {done}/{total} done ({pct}%)", out)
        self.assertIn("# Team checklist - March 2026", out)

    def test_percent_shows_one_decimal_below_ten(self):
        self.assertEqual(generate.percent(1, 36), "2.8")
        self.assertEqual(generate.percent(1, 20), "5.0")
        self.assertEqual(generate.percent(1, 10), "10")
        self.assertEqual(generate.percent(2, 3), "67")
        self.assertEqual(generate.percent(0, 5), "0")
        self.assertEqual(generate.percent(0, 0), "0")

    def test_team_checklist_week_counts_only_the_week(self):
        tasks_file = self.root / "pmo/registers/tasks.yaml"
        tasks_file.write_text(tasks_file.read_text(encoding="utf-8")
                              + "  - {id: T-90, title: In week, status: not-started, due: 2026-03-12}\n"
                              + "  - {id: T-91, title: Later in month, status: not-started, due: 2026-03-30}\n", encoding="utf-8")
        code, out, err = tool("generate.py", self.root, "team-checklist", "--week", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("`T-90`", out)
        self.assertNotIn("`T-91`", out)

    def test_names_with_quotes_keep_the_front_matter_valid(self):
        cfg_path = self.root / "pmo/config.yaml"
        cfg_path.write_text(cfg_path.read_text(encoding="utf-8").replace("name: Acme Portal", "name: 'Acme \"Portal\" \\ Co'"), encoding="utf-8")
        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout")
        self.assertEqual(code, 0, err)
        fm, _ = pc.split_front_matter(out, strict=True)
        self.assertEqual(fm["project"], 'Acme "Portal" \\ Co')

    def test_empty_open_questions_written_as_none(self):
        code, out, err = tool("generate.py", self.root, "status-report", "2026-03", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.endswith("## Open questions\n- None\n"), repr(out[-40:]))
        self.assertNotIn("- {{question}}", out)

    def test_bad_register_config_exits_2(self):
        cfg_path = self.root / "pmo/config.yaml"
        cfg_path.write_text(cfg_path.read_text(encoding="utf-8") + "registers:\n  tasks:\n    blocked: [stuck]\n", encoding="utf-8")
        code, _, err = tool("generate.py", self.root, "decision-log", "--stdout")
        self.assertEqual(code, 2)
        self.assertIn("ERROR config", err)
        self.assertNotIn("Traceback", err)

    def test_project_plan_on_acme(self):
        risks_file = self.root / "pmo/registers/risks.yaml"
        risks_text = risks_file.read_text(encoding="utf-8")
        risks_file.write_text(risks_text + "  - {id: R-99, title: Fake closed risk, probability: low, impact: low, owner: sam, mitigation: none, status: closed, origin: stated, raised: 2026-02-10, closed: 2026-03-01}\n", encoding="utf-8")

        code, out, err = tool("generate.py", self.root, "project-plan", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)

        # Team table has the three roster names
        self.assertIn("Sam Example", out)
        self.assertIn("Alice Example", out)
        self.assertIn("Bob Example", out)

        # Every Acme goal appears as a ### block
        self.assertIn("### P-1 - Launch portal beta", out)
        self.assertIn("### P-2 - Publish user guide", out)

        # Open risks only
        self.assertIn("R-1", out)
        self.assertIn("Vendor delay", out)
        self.assertNotIn("R-2", out)
        self.assertNotIn("R-99", out)

        # The change-log row comes from an approved change
        self.assertIn("Drop the export page", out)
        self.assertIn("2026-02-22", out)
        self.assertNotIn("Add dark mode", out)

    def test_project_plan_notes_missing_due(self):
        tasks_file = self.root / "pmo/registers/tasks.yaml"
        text = tasks_file.read_text(encoding="utf-8").replace("due: 2026-03-10", "due: null")
        tasks_file.write_text(text, encoding="utf-8")

        code, out, err = tool("generate.py", self.root, "project-plan", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("1 open tasks have no due date", err)

    def test_status_report_progress_by_sub_project_only_when_tagged(self):
        args = ("status-report", "2026-03", "--as-of", "2026-03-15", "--stdout")
        out = tool("generate.py", self.root, *args)[1]
        self.assertNotIn("Progress by sub-project", out)
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8")
                            + "\nsubprojects:\n  api: {}\n  web: {}\nregisters:\n  tasks:\n    fields: [id, title, team, group, priority, owner, status, due, done_on, period, notes, origin, tests, subproject]\n    enums: {subproject: subprojects}\n",
                            encoding="utf-8")
        self.assertNotIn("Progress by sub-project", tool("generate.py", self.root, *args)[1])  # configured, but no task is tagged
        tasks_file = self.root / "pmo/registers/tasks.yaml"
        tasks_file.write_text(tasks_file.read_text(encoding="utf-8").replace("{id: T-3,", "{id: T-3, subproject: api,").replace("{id: T-4,", "{id: T-4, subproject: web,"), encoding="utf-8")
        code, out, err = tool("generate.py", self.root, *args)
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"## Progress by sub-project\n\n\| Sub-project \| Tasks \| Done \| Blocked \|\n\|---\|---\|---\|---\|\n\| api \| 1 \| 1 \| 0 \|\n\| web \| 1 \| 0 \| 1 \|\n\| not set \|")
        self.assertLess(out.index("## Progress by team"), out.index("## Progress by sub-project"))
        self.assertLess(out.index("## Progress by sub-project"), out.index("## Completed since last report"))

    def test_status_report_month_on_acme(self):
        code, out, err = tool("generate.py", self.root, "status-report", "2026-03", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)

        # Overall is red with T-1 in reason
        self.assertRegex(out, r"\*\*Overall:\*\* red - top-priority task T-1 is overdue")

        # Priority table has rows high, medium, low in that order
        idx_high = out.index("| high |")
        idx_med = out.index("| medium |")
        idx_low = out.index("| low |")
        self.assertTrue(idx_high < idx_med < idx_low)

        # Blocked count for medium is 1 (T-4)
        self.assertRegex(out, r"\|\s*medium\s*\|\s*0\s*/\s*2\s*\|\s*0\s*\|\s*1\s*\|\s*amber\s*\|\s*\{\{comment\}\}\s*\|")

        # {{comment}}, {{changes}}, {{delta}} remain
        self.assertIn("{{comment}}", out)
        self.assertIn("{{changes}}", out)
        self.assertIn("{{delta}}", out)

        # Notes on data has the RAG line
        self.assertIn("- RAG rule: weekly-status; overdue measured at 2026-03-15; registers read on 2026-03-15.", out)

    def test_status_report_week(self):
        code, out, err = tool("generate.py", self.root, "status-report", "2026-W11", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("Tasks counted: period 2026-03;", out)

    def test_status_report_week_crossing_months(self):
        # 2026-W09 runs Mon 23 Feb to Sun 1 Mar: 6 of its 7 days are February, so it counts February
        code, out, err = tool("generate.py", self.root, "status-report", "2026-W09", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("Tasks counted: period 2026-02;", out)

    def test_status_report_refuses_existing(self):
        code, out, err = tool("generate.py", self.root, "status-report", "2026-03")
        self.assertEqual(code, 3)
        self.assertIn("already exists", err)

    def _assert_generated_draft_placeholders(self, args, expected_placeholders):
        import structure_check
        cfg = pc.load_config(self.root)
        code, out, err = tool("generate.py", self.root, *args, "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)
        errs, warns = structure_check.check(self.root, cfg, out)
        want = ["unreplaced {{placeholder}} left in text"] if expected_placeholders else []
        self.assertEqual(errs, want, f"{args[0]} unexpected errors: {errs}")
        found = set(re.findall(r"\{\{(.*?)\}\}", structure_check.strip_fences(out)))
        self.assertEqual(found, expected_placeholders, f"{args[0]} placeholders mismatch")

    def test_both_pass_structure_check_except_placeholders(self):
        self._assert_generated_draft_placeholders(("project-plan",), {"item", "target"})
        self._assert_generated_draft_placeholders(
            ("status-report", "2026-03"),
            {
                "3 sentences at most: what moved, what did not, what is next",
                "changes",
                "comment",
                "delta",
                "id",
                "new, changed or closed risk or issue",
                "task",
            },
        )

    def test_team_checklist_passes_structure_check_except_placeholders(self):
        self._assert_generated_draft_placeholders(("team-checklist", "2026-03"), set())

    def test_scope_wbs_groups_tasks_by_area(self):
        self._assert_generated_draft_placeholders(("scope-wbs",), {"deliverable", "exclusion", "assumption"})
        code, out, _ = tool("generate.py", self.root, "scope-wbs", "--stdout")
        self.assertIn("| ui | Design login page; Pick a payment vendor | Bob Example | not set | `T-2`, `T-4`, `REQ-1` |", out)
        self.assertIn("| docs | Write API outline | Alice Example | not set | `T-3` |", out)

    def test_work_order_lists_open_tasks_by_person_then_due_date(self):
        self._assert_generated_draft_placeholders(("work-order",), {"title", "purpose", "scope item", "criterion", "budget and constraints"})
        code, out, _ = tool("generate.py", self.root, "work-order", "--as-of", "2026-03-15", "--stdout")
        self.assertIn("**Assigned to:** Alice Example, Bob Example", out)
        self.assertIn("**Due:** 2026-04-01", out)
        self.assertLess(out.index("`T-1`"), out.index("`T-2`"))  # grouped by person in roster order
        self.assertLess(out.index("`T-2`"), out.index("`T-4`"))  # then by due date
        self.assertNotIn("`T-3`", out)  # done, so not open

    def test_delivery_report_counts_and_carries_over(self):
        self._assert_generated_draft_placeholders(
            ("delivery-report", "2026-03"),
            {"id", "output", "lead", "delivered", "acceptance_met", "evidence", "title", "status", "item", "reason", "plan"})
        code, out, _ = tool("generate.py", self.root, "delivery-report", "2026-03", "--as-of", "2026-03-15", "--stdout")
        self.assertIn("**Planned:** 4 tasks - **Delivered:** 1 (25%) - **Dropped:** 0 - **Carried over:** 3", out)
        self.assertIn("- Write API outline `T-3` - Alice Example - 2026-03-05", out)
        self.assertIn("| M-1 | Staging ready | 2026-03-20 | in-progress |", out)
        self.assertIn("- Pick a payment vendor `T-4`", out.split("## Carried to next period")[1])

    def test_defect_gap_report_lists_failed_tests_issues_and_gaps(self):
        self._assert_generated_draft_placeholders(
            ("defect-gap-report", "2026-03"),
            {"At most three sentences summarizing quality state, critical defects, and release readiness.", "recommendation naming an ID"})
        code, out, _ = tool("generate.py", self.root, "defect-gap-report", "2026-03", "--as-of", "2026-03-15", "--stdout")
        self.assertIn("**Failed tests:** 1 - **Open issues:** 3 - **Requirements without a passing test:** 2", out)
        self.assertIn("| TST-2 | Login with valid credentials | REQ-1 | I-3 | high | Bob Example |", out)
        self.assertLess(out.index("| I-3 |"), out.index("| I-1 |"))  # most severe first
        self.assertNotIn("| I-4 |", out)  # resolved
        self.assertIn("| REQ-1 | Users can log in | high | test failed |", out)
        self.assertIn("| REQ-2 | Pages load fast | medium | no test |", out)

    def test_non_english_draft_language_exits_2(self):
        cfg_path = self.root / "pmo/config.yaml"
        base = re.sub(r"(?m)^languages:.*\n(?:[ \t#].*\n|\n)*", "", cfg_path.read_text(encoding="utf-8"))
        cfg_path.write_text(base + "\nlanguages:\n  draft: xx\n  xx: {label: XX, dir: rtl}\n", encoding="utf-8")
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()
        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout")
        self.assertEqual(code, 2)
        self.assertIn("generator: null", err)
        self.assertFalse(doc.exists())

    def test_english_with_translations_still_generates(self):
        cfg_path = self.root / "pmo/config.yaml"
        base = re.sub(r"(?m)^languages:.*\n(?:[ \t#].*\n|\n)*", "", cfg_path.read_text(encoding="utf-8"))
        cfg_path.write_text(base + "\nlanguages:\n  draft: en\n  translations: [xx]\n  en: {label: EN, dir: ltr}\n  xx: {label: XX, dir: rtl}\n", encoding="utf-8")
        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("Decision log", out)


if __name__ == "__main__":
    unittest.main()
