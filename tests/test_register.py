"""Tests for scripts/register.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_register"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
TOOL = SCRIPTS / "register.py"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import pmo_common as pc  # noqa: E402
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def run(project, *args):
    p = subprocess.run([sys.executable, str(TOOL), "--project", str(project), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class RegisterSet(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_updates_fields_preserving_other_lines_and_comments(self):
        tasks_path = self.root / "pmo/registers/tasks.yaml"
        raw = tasks_path.read_text(encoding="utf-8")
        tasks_path.write_text("# keep this comment\n" + raw, encoding="utf-8")
        before_lines = tasks_path.read_text(encoding="utf-8").splitlines()

        code, out, err = run(self.root, "set", "tasks", "T-001", "status=done", "due=2026-03-18", "notes=All set")
        self.assertEqual(code, 0, err)
        self.assertIn("updated: tasks T-001", out)

        after_lines = tasks_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(after_lines[0], "# keep this comment")
        self.assertEqual(after_lines[1], before_lines[1])
        self.assertEqual(after_lines[3:], before_lines[3:])

        entry = next(e for e in pc.load_register(self.root, pc.load_config(self.root), "tasks") if e["id"] == "T-001")
        self.assertEqual(entry["status"], "done")
        self.assertEqual(str(entry["due"]), "2026-03-18")
        self.assertEqual(entry["notes"], "All set")

        rv = subprocess.run([sys.executable, str(SCRIPTS / "render_views.py"), "--project", str(self.root)],
                            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(rv.returncode, 0, rv.stdout + rv.stderr)
        rv_chk = subprocess.run([sys.executable, str(SCRIPTS / "render_views.py"), "--project", str(self.root), "--check"],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(rv_chk.returncode, 0, rv_chk.stdout + rv_chk.stderr)

    def test_short_unpadded_id_resolves(self):
        code, out, err = run(self.root, "set", "tasks", "T-1", "status=done")
        self.assertEqual(code, 0, err)
        self.assertIn("updated: tasks T-001", out)
        entry = next(e for e in pc.load_register(self.root, pc.load_config(self.root), "tasks") if e["id"] == "T-001")
        self.assertEqual(entry["status"], "done")

    def test_null_clears_and_empty_writes_empty_string(self):
        code, out, err = run(self.root, "set", "tasks", "T-001", "due=null", "notes=")
        self.assertEqual(code, 0, err)
        entry = next(e for e in pc.load_register(self.root, pc.load_config(self.root), "tasks") if e["id"] == "T-001")
        self.assertIsNone(entry["due"])
        self.assertEqual(entry["notes"], "")
        rv = subprocess.run([sys.executable, str(SCRIPTS / "render_views.py"), "--project", str(self.root)],
                            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(rv.returncode, 0, rv.stdout + rv.stderr)

    def test_list_wbs_boolean_words_and_special_chars(self):
        code, out, err = run(
            self.root, "set", "tasks", "T-001",
            "tests=[TST-001]", "wbs=1.2", "notes=no", "title=Waiting: phase 2, urgent (تحديث)"
        )
        self.assertEqual(code, 0, err)
        entry = next(e for e in pc.load_register(self.root, pc.load_config(self.root), "tasks") if e["id"] == "T-001")
        self.assertEqual(entry["tests"], ["TST-001"])
        self.assertEqual(entry["wbs"], "1.2")
        self.assertIsInstance(entry["wbs"], str)
        self.assertEqual(entry["notes"], "no")
        self.assertIsInstance(entry["notes"], str)
        self.assertEqual(entry["title"], "Waiting: phase 2, urgent (تحديث)")
        rv = subprocess.run([sys.executable, str(SCRIPTS / "render_views.py"), "--project", str(self.root)],
                            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(rv.returncode, 0, rv.stdout + rv.stderr)

    def test_roster_by_slug_and_capacity_by_period_person(self):
        code, out, err = run(self.root, "set", "roster", "alice", "role=Lead Engineer")
        self.assertEqual(code, 0, err)
        self.assertIn("updated: roster alice", out)
        alice = next(e for e in pc.load_register(self.root, pc.load_config(self.root), "roster") if e["slug"] == "alice")
        self.assertEqual(alice["role"], "Lead Engineer")

        code, out, err = run(self.root, "set", "capacity", "2026-03/alice", "leave_days=5")
        self.assertEqual(code, 0, err)
        self.assertIn("updated: capacity 2026-03/alice", out)
        cap = next(e for e in pc.load_register(self.root, pc.load_config(self.root), "capacity") if e["person"] == "alice")
        self.assertEqual(cap["leave_days"], 5)

    def test_validation_failures_exit_1_and_leave_file_untouched(self):
        tasks_path = self.root / "pmo/registers/tasks.yaml"
        before = tasks_path.read_bytes()
        secret = "Example-Pa55-zz99"
        bad_cases = (
            ("status=bogus", "not in"),
            ("due=2026-02-30", "YYYY-MM-DD"),
            ("owner=nobody", "not in the roster"),
            ("goal=GL-999", "not an id in goals"),
            ("bogus_field=1", "unexpected field"),
            (f"notes=password={secret}", "looks like a credential"),
        )
        for assignment, expected_msg in bad_cases:
            with self.subTest(assignment=assignment):
                code, out, err = run(self.root, "set", "tasks", "T-001", assignment)
                self.assertEqual(code, 1, out + err)
                self.assertIn(expected_msg, err)
                self.assertNotIn(secret, out + err)
                self.assertEqual(tasks_path.read_bytes(), before)

    def test_refuses_changing_immutable_keys(self):
        for args in (
            ("tasks", "T-001", "id=T-099"),
            ("roster", "alice", "slug=ally"),
            ("capacity", "2026-03/alice", "period=2026-04"),
            ("capacity", "2026-03/alice", "person=bob"),
        ):
            with self.subTest(args=args):
                code, _, err = run(self.root, "set", *args)
                self.assertEqual(code, 2)
                self.assertIn("cannot change", err)

    def test_unchanged_exits_0_and_does_not_rewrite(self):
        tasks_path = self.root / "pmo/registers/tasks.yaml"
        before = tasks_path.read_bytes()
        code, out, err = run(self.root, "set", "tasks", "T-001", "status=in-progress", "due=2026-03-10")
        self.assertEqual(code, 0, err)
        self.assertIn("unchanged: tasks T-001", out)
        self.assertEqual(tasks_path.read_bytes(), before)

    def test_usage_and_lookup_errors_exit_2(self):
        (self.root / "pmo/registers/facts.yaml").unlink(missing_ok=True)
        for args in (
            ("set", "nope", "T-001", "status=done"),
            ("set", "facts", "FACT-001", "status=active"),
            ("set", "tasks", "T-999", "status=done"),
            ("set", "tasks", "T-001", "status"),
            ("set", "tasks", "T-001", "=done"),
            ("set", "tasks", "T-001", "status=done", "status=blocked"),
            ("set", "capacity", "alice", "leave_days=1"),
        ):
            with self.subTest(args=args):
                code, _, err = run(self.root, *args)
                self.assertEqual(code, 2, err)
                self.assertIn("ERROR", err)
        code, _, err = run(self.root / "missing-proj", "set", "tasks", "T-001", "status=done")
        self.assertEqual(code, 2)

    def test_works_via_launcher(self):
        launcher_src = REPO / "skills/pmo-docs/assets/starter/bin/pmo"
        launcher = self.root / "pmo/bin/pmo"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(launcher_src, launcher)
        launcher.chmod(0o755)
        env = {**os.environ, "PMO_DOCS_SKILL": str(REPO / "skills/pmo-docs")}
        p = subprocess.run(
            [str(launcher), "register", "set", "tasks", "T-002", "status=in-progress"],
            cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("updated: tasks T-002", p.stdout)

    def test_help(self):
        p = subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0)
        self.assertIn("usage", p.stdout.lower())
        self.assertIn("Exit codes", p.stdout)


if __name__ == "__main__":
    unittest.main()
