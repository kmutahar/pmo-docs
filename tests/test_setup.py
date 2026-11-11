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
        self.assertTrue((self.root / "pmo/bin/pmo").is_file())
        self.assertEqual((self.root / "pmo/bin/pmo").stat().st_mode & 0o777, 0o755)
        cfg = pc.load_config(self.root)
        self.assertEqual(cfg["project"]["name"], "Demo")
        self.assertEqual(cfg["project"]["manager"], "Pat Example")
        optional = {"requirements", "tests", "environments", "permissions"}
        self.assertEqual(len(cfg["registers"]), 20)
        for name, reg in cfg["registers"].items():
            dest = self.root / cfg["paths"]["registers"] / reg["file"]
            self.assertEqual(dest.exists(), name not in optional, name)
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

    def test_week_start_flag(self):
        # --week-start saturday writes it
        tool("setup.py", self.root, "--name", "Demo", "--week-start", "saturday")
        cfg = pc.load_config(self.root)
        self.assertEqual(cfg["project"]["week_start"], "saturday")
        import yaml
        mine = yaml.safe_load((self.root / "pmo/config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(mine["project"]["week_start"], "saturday")

    def test_week_start_monday_omitted_from_sparse_config(self):
        # --week-start monday writes nothing for it
        tool("setup.py", self.root, "--name", "Demo", "--week-start", "monday")
        import yaml
        mine = yaml.safe_load((self.root / "pmo/config.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("week_start", mine["project"])

    def test_week_start_bad_day_exits_2_and_writes_nothing(self):
        code, out, err = tool("setup.py", self.root, "--name", "Demo", "--week-start", "someday")
        self.assertEqual(code, 2)
        self.assertFalse((self.root / "pmo").exists())

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
        self.assertIn("pmo/bin/pmo render_views --check", out)

    def test_launcher_flag_on_existing_project(self):
        tool("setup.py", self.root, "--name", "Demo")
        (self.root / "pmo/bin/pmo").unlink()
        code, out, err = tool("setup.py", self.root, "--launcher")
        self.assertEqual(code, 0, err)
        self.assertIn("created: pmo/bin/pmo", out)
        self.assertTrue((self.root / "pmo/bin/pmo").is_file())
        self.assertEqual((self.root / "pmo/bin/pmo").stat().st_mode & 0o777, 0o755)
        code, out, err = tool("setup.py", self.root, "--launcher")
        self.assertEqual(code, 0, err)
        self.assertIn("kept: pmo/bin/pmo", out)

    def test_launcher_flag_existing_differs_exits_1(self):
        tool("setup.py", self.root, "--name", "Demo")
        (self.root / "pmo/bin/pmo").write_text("custom content\n", encoding="utf-8")
        code, out, err = tool("setup.py", self.root, "--launcher")
        self.assertEqual(code, 1)
        self.assertIn("differs", out + err)
        self.assertEqual((self.root / "pmo/bin/pmo").read_text(encoding="utf-8"), "custom content\n")

    def test_fresh_setup_existing_differs_exits_1_and_writes_nothing(self):
        (self.root / "pmo/bin").mkdir(parents=True)
        (self.root / "pmo/bin/pmo").write_text("custom content\n", encoding="utf-8")
        code, out, err = tool("setup.py", self.root, "--name", "Demo")
        self.assertEqual(code, 1)
        self.assertIn("differs", out + err)
        self.assertFalse((self.root / "pmo/config.yaml").exists())

    def test_fresh_setup_existing_matches_kept(self):
        starter = REPO / "skills/pmo-docs/assets/starter/bin/pmo"
        (self.root / "pmo/bin").mkdir(parents=True)
        shutil.copyfile(starter, self.root / "pmo/bin/pmo")
        code, out, err = tool("setup.py", self.root, "--name", "Demo")
        self.assertEqual(code, 0, err)
        self.assertIn("kept: pmo/bin/pmo", out)

    def test_bad_flag_values_exit_2(self):
        self.assertEqual(tool("setup.py", self.root, "--bogus-flag")[0], 2)
        self.assertFalse((self.root / "pmo").exists())

    def test_missing_project_folder_exits_2(self):
        self.assertEqual(tool("setup.py", self.root / "nope")[0], 2)

    def test_help(self):
        self.assertEqual(tool("setup.py", self.root, "--help")[0], 0)


if __name__ == "__main__":
    unittest.main()
