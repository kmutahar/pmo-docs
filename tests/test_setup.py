"""Tests for scripts/setup.py on an empty temp folder. Run from the repo root: python3 -m unittest tests.test_setup"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
import pmo_common as pc  # noqa: E402


def tool(name, project, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / name), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class Setup(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "proj"
        self.root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_creates_a_project_that_validates(self):
        code, out, err = tool("setup.py", self.root, "--name", "Demo", "--manager", "Pat Example")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.root / "pmo/config.yaml").exists())
        self.assertTrue((self.root / "pmo/house-rules.md").exists())
        self.assertTrue((self.root / "pmo/documents").is_dir())
        cfg = pc.load_config(self.root)
        self.assertEqual(cfg["project"]["name"], "Demo")
        self.assertEqual(cfg["project"]["manager"], "Pat Example")
        for reg in cfg["registers"].values():
            self.assertTrue((self.root / cfg["paths"]["registers"] / reg["file"]).exists(), reg["file"])
        self.assertEqual(tool("render_views.py", self.root, "--check")[0], 0)
        self.assertEqual(tool("docs_audit.py", self.root)[0], 0)
        self.assertEqual(tool("structure_check.py", self.root)[0], 0)

    def test_config_is_sparse(self):
        tool("setup.py", self.root, "--name", "Demo")
        import yaml
        mine = yaml.safe_load((self.root / "pmo/config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(mine), {"schema_version", "project"})
        self.assertEqual(mine["project"], {"name": "Demo", "manager": None})  # unknown values stay null

    def test_priority_order_flag(self):
        tool("setup.py", self.root, "--priority-order", "urgent,normal")
        cfg = pc.load_config(self.root)
        self.assertEqual(cfg["vocab"]["priority_order"], ["urgent", "normal"])

    def test_never_overwrites(self):
        tool("setup.py", self.root, "--name", "First")
        reg = self.root / "pmo/registers/tasks.yaml"
        reg.write_text("tasks:\n  - {id: T-1, title: Mine, status: done}\n", encoding="utf-8")
        before = (self.root / "pmo/config.yaml").read_text(encoding="utf-8")
        code, out, _ = tool("setup.py", self.root, "--name", "Second")
        self.assertEqual(code, 0)
        self.assertIn("already", out.lower())
        self.assertEqual((self.root / "pmo/config.yaml").read_text(encoding="utf-8"), before)
        self.assertIn("Mine", reg.read_text(encoding="utf-8"))

    def test_existing_register_is_kept_when_config_is_missing(self):
        (self.root / "pmo/registers").mkdir(parents=True)
        reg = self.root / "pmo/registers/tasks.yaml"
        reg.write_text("tasks:\n  - {id: T-1, title: Mine, status: done}\n", encoding="utf-8")
        self.assertEqual(tool("setup.py", self.root)[0], 0)
        self.assertIn("Mine", reg.read_text(encoding="utf-8"))

    def test_newer_schema_version_in_check_mode_exits_2(self):
        (self.root / "pmo").mkdir()
        (self.root / "pmo/config.yaml").write_text("schema_version: 99\n", encoding="utf-8")
        code, out, err = tool("setup.py", self.root)
        self.assertEqual(code, 2, out + err)

    def test_failing_view_render_exits_1_with_errors(self):
        (self.root / "pmo/registers").mkdir(parents=True)
        (self.root / "pmo/registers/tasks.yaml").write_text("tasks:\n  - {id: T-1, title: x, bogus_field: 1}\n", encoding="utf-8")
        code, out, _ = tool("setup.py", self.root)
        self.assertEqual(code, 1)
        self.assertIn("ERROR", out)

    def test_string_exit_from_render_views_is_reported(self):
        import io, contextlib, setup, render_views
        out = io.StringIO()
        with mock.patch.object(render_views, "main", side_effect=SystemExit("boom")), contextlib.redirect_stdout(out):
            code = setup.main(["--project", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("boom", out.getvalue())

    def test_prints_hook_line(self):
        out = tool("setup.py", self.root)[1]
        self.assertIn("render_views.py --check", out)

    def test_bad_flag_values_exit_2(self):
        self.assertEqual(tool("setup.py", self.root, "--bogus-flag")[0], 2)
        self.assertFalse((self.root / "pmo").exists())

    def test_missing_project_folder_exits_2(self):
        self.assertEqual(tool("setup.py", self.root / "nope")[0], 2)

    def test_help(self):
        self.assertEqual(tool("setup.py", self.root, "--help")[0], 0)


if __name__ == "__main__":
    unittest.main()
