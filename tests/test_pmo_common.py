"""Tests for scripts/pmo_common.py. Run from the repo root: python3 -m unittest discover tests"""
import datetime
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


class Common(unittest.TestCase):
    def project(self, config=None, register=None):
        d = Path(tempfile.mkdtemp())
        (d / "pmo/registers").mkdir(parents=True)
        if config is not None:
            (d / "pmo/config.yaml").write_text(config, encoding="utf-8")
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

    def test_newer_schema_refused(self):
        with self.assertRaises(SystemExit):
            pc.load_config(self.project("schema_version: 99\n"))

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

    def test_config_errors_reports_week_start(self):
        import render_views
        cfg = pc.load_config(Path(__file__).resolve().parents[1] / "examples/acme")
        cfg["project"]["week_start"] = "someday"
        errs = render_views.config_errors(cfg)
        self.assertTrue(any("week_start" in e and "someday" in e for e in errs))


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


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"
TOOLS = ["docs_audit.py", "generate.py", "overdue.py", "render_views.py", "setup.py", "structure_check.py", "where.py"]


class EveryTool(unittest.TestCase):
    def run_tool(self, name, *args):
        p = subprocess.run([sys.executable, str(SCRIPTS / name), *args], capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout + p.stderr

    def test_every_tool_answers_help(self):
        for name in TOOLS:
            code, out = self.run_tool(name, "--help")
            self.assertEqual(code, 0, name)
            self.assertIn("usage", out.lower(), name)

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


if __name__ == "__main__":
    unittest.main()
