"""Tests for scripts/generate.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_generate"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
import pmo_common as pc  # noqa: E402


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
        errs, warns = structure_check.check(self.root, cfg, doc.read_text(encoding="utf-8"))
        # The only errors allowed are leftover-placeholder and HTML-comment errors
        allowed_pats = [r"unreplaced \{\{placeholder\}\}"]
        disallowed = [e for e in errs if not any(re.search(p, e) for p in allowed_pats)]
        self.assertEqual(disallowed, [], f"Disallowed errors: {disallowed}")

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

    def test_untouched_blocks_keep_trailing_spaces(self):
        code, out, err = tool("generate.py", self.root, "status-report", "2026-03", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.endswith("## Open questions\n- {{question}}\n"), repr(out[-40:]))

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

    def test_both_pass_structure_check_except_placeholders(self):
        import structure_check
        cfg = pc.load_config(self.root)
        allowed_pats = [r"unreplaced \{\{placeholder\}\}"]

        # 1. Project plan
        code, out, err = tool("generate.py", self.root, "project-plan", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)
        errs, warns = structure_check.check(self.root, cfg, out)
        disallowed = [e for e in errs if not any(re.search(p, e) for p in allowed_pats)]
        self.assertEqual(disallowed, [], f"Project plan disallowed errors: {disallowed}")

        # 2. Status report
        code, out, err = tool("generate.py", self.root, "status-report", "2026-03", "--as-of", "2026-03-15", "--stdout")
        self.assertEqual(code, 0, err)
        errs, warns = structure_check.check(self.root, cfg, out)
        disallowed = [e for e in errs if not any(re.search(p, e) for p in allowed_pats)]
        self.assertEqual(disallowed, [], f"Status report disallowed errors: {disallowed}")

    def test_non_english_draft_language_exits_2(self):
        cfg_path = self.root / "pmo/config.yaml"
        cfg_path.write_text(cfg_path.read_text(encoding="utf-8") + "\nlanguages:\n  draft: xx\n  xx: {label: XX, dir: rtl}\n", encoding="utf-8")
        doc = self.root / "pmo/documents/Decision log.md"
        if doc.exists():
            doc.unlink()
        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout")
        self.assertEqual(code, 2)
        self.assertIn("generator: null", err)
        self.assertFalse(doc.exists())

    def test_english_with_translations_still_generates(self):
        cfg_path = self.root / "pmo/config.yaml"
        cfg_path.write_text(cfg_path.read_text(encoding="utf-8") + "\nlanguages:\n  draft: en\n  translations: [xx]\n  en: {label: EN, dir: ltr}\n  xx: {label: XX, dir: rtl}\n", encoding="utf-8")
        code, out, err = tool("generate.py", self.root, "decision-log", "--stdout")
        self.assertEqual(code, 0, err)
        self.assertIn("Decision log", out)


if __name__ == "__main__":
    unittest.main()
