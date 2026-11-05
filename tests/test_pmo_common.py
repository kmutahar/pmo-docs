"""Tests for scripts/pmo_common.py. Run from the repo root: python3 -m unittest discover tests"""
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


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"
TOOLS = ["docs_audit.py", "overdue.py", "render_views.py", "setup.py", "structure_check.py", "where.py"]


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
        for f in SCRIPTS.glob("*.py"):
            text = f.read_text(encoding="utf-8")
            self.assertFalse(re.search(r"""["']git["']|git (add|commit|push)""", text), f.name)


if __name__ == "__main__":
    unittest.main()
