"""Tests for test evidence in the tasks view on a temp copy of examples/acme.
Run from repo root: python3 -m unittest tests.test_test_evidence
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RENDER_VIEWS = REPO / "skills/pmo-docs/scripts/render_views.py"
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402


def run_render(project, *args):
    p = subprocess.run([sys.executable, str(RENDER_VIEWS), "--project", str(project), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class TestEvidence(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        self.views = self.root / "pmo/views"
        self.cfg_file = self.root / "pmo/config.yaml"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def write_config(self, extra):
        cfg = pc.yaml.safe_load(self.cfg_file.read_text(encoding="utf-8")) or {}
        merged = pc.merge(cfg, extra)
        self.cfg_file.write_text(pc.yaml.safe_dump(merged), encoding="utf-8")

    def test_acme_lists_no_done_task_without_a_test(self):
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)
        tasks_view = (self.views / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Done without a linked test:** none", tasks_view)

    def test_done_task_without_a_test_is_listed(self):
        tasks_path = self.reg / "tasks.yaml"
        text = tasks_path.read_text(encoding="utf-8")
        # Change T-2 from not-started to done
        text = text.replace("status: not-started", "status: done")
        tasks_path.write_text(text, encoding="utf-8")
        # In Acme, TST-2 points to T-2; clear task link on TST-2 so T-2 has no linked test
        tests_path = self.reg / "tests.yaml"
        tests_text = tests_path.read_text(encoding="utf-8").replace("task: T-2", "task: null")
        tests_path.write_text(tests_text, encoding="utf-8")

        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)
        tasks_view = (self.views / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Done without a linked test:** T-2", tasks_view)
        line = [ln for ln in tasks_view.splitlines() if "**Done without a linked test:**" in ln][0]
        self.assertIn("T-2", line)
        self.assertNotIn("T-3", line)

    def test_link_works_in_both_directions(self):
        tasks_path = self.reg / "tasks.yaml"
        tests_path = self.reg / "tests.yaml"

        # Remove tests: [TST-1] from T-3
        tasks_text = tasks_path.read_text(encoding="utf-8").replace(", tests: [TST-1]", "")
        tasks_path.write_text(tasks_text, encoding="utf-8")

        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)
        tasks_view = (self.views / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Done without a linked test:** none", tasks_view)

        # Remove task: T-3 from TST-1 as well
        tests_text = tests_path.read_text(encoding="utf-8").replace("task: T-3", "task: null")
        tests_path.write_text(tests_text, encoding="utf-8")

        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)
        tasks_view = (self.views / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Done without a linked test:** T-3", tasks_view)

    def test_view_unchanged_without_tests_entries(self):
        (self.reg / "tests.yaml").write_text("tests: []\n", encoding="utf-8")
        tasks_path = self.reg / "tasks.yaml"
        tasks_path.write_text(tasks_path.read_text(encoding="utf-8").replace(", tests: [TST-1]", ""), encoding="utf-8")
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)
        tasks_view = (self.views / "tasks.md").read_text(encoding="utf-8")
        self.assertNotIn("Done without", tasks_view)

    def test_done_status_comes_from_config(self):
        self.write_config({"registers": {"tasks": {"done": ["dropped"]}}})
        # Set T-4 to dropped (has no test) and unlink T-3's test, so T-3 (still `done`) would be listed if `done` still counted
        tasks_path = self.reg / "tasks.yaml"
        text = tasks_path.read_text(encoding="utf-8").replace("status: blocked", "status: dropped").replace(", tests: [TST-1]", "")
        tasks_path.write_text(text, encoding="utf-8")
        tests_path = self.reg / "tests.yaml"
        tests_path.write_text(tests_path.read_text(encoding="utf-8").replace("task: T-3", "task: null"), encoding="utf-8")

        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)
        tasks_view = (self.views / "tasks.md").read_text(encoding="utf-8")
        line = [ln for ln in tasks_view.splitlines() if "**Done without a linked test:**" in ln][0]
        self.assertIn("T-4", line)
        self.assertNotIn("T-3", line)

    def test_unknown_done_status_is_a_config_error(self):
        self.write_config({"registers": {"tasks": {"done": ["finished"]}}})
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 2)
        self.assertIn("config: registers.tasks.done status `finished` not in vocab.task_status", out)

    def test_linked_tests_ignores_unknown_ids(self):
        data = {
            "tasks": [{"id": "T-1", "tests": ["TST-99"]}],
            "tests": [{"id": "TST-1", "task": "T-2"}],
        }
        res = render_views.linked_tests(data, "T-1")
        self.assertEqual(res, [])


if __name__ == "__main__":
    unittest.main()
