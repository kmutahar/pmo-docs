"""Tests for the requirements, tests, environments and permissions registers on a temp copy of examples/acme.
Run from repo root: python3 -m unittest tests.test_new_registers
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RENDER_VIEWS = REPO / "skills/pmo-docs/scripts/render_views.py"
SETUP = REPO / "skills/pmo-docs/scripts/setup.py"
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


def run_render(project, *args):
    p = subprocess.run([sys.executable, str(RENDER_VIEWS), "--project", str(project), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def run_setup(project, *args):
    p = subprocess.run([sys.executable, str(SETUP), "--project", str(project), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class NewRegisters(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        self.views = self.root / "pmo/views"
        self.cfg_file = self.root / "pmo/config.yaml"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def append(self, name, line):
        with open(self.reg / f"{name}.yaml", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def write_config(self, extra):
        cfg = pc.yaml.safe_load(self.cfg_file.read_text(encoding="utf-8")) or {}
        merged = pc.merge(cfg, extra)
        self.cfg_file.write_text(pc.yaml.safe_dump(merged), encoding="utf-8")

    def test_acme_validates_with_the_four_registers(self):
        code, out, _ = run_render(self.root, "--check")
        self.assertEqual(code, 0, out)
        for v in ("requirements.md", "tests.md", "environments.md", "permissions.md"):
            self.assertTrue((self.views / v).exists(), f"missing view {v}")

    def test_ids_use_the_prefixes(self):
        # every Acme entry matches its register's prefix; an entry with a bad id gives an error naming the expected form
        for name, prefix in (("requirements", "REQ"), ("tests", "TST"), ("environments", "ENV"), ("permissions", "PERM")):
            path = self.reg / f"{name}.yaml"
            original = path.read_text(encoding="utf-8")
            entries = pc.yaml.safe_load(original)[name]
            self.assertTrue(entries and all(e["id"].startswith(prefix + "-") for e in entries), name)
            first = [ln for ln in original.splitlines() if ln.startswith("  - ")][0]
            self.append(name, first.replace(f"id: {prefix}-1,", f"id: {prefix}-x,"))
            code, out, _ = run_render(self.root)
            self.assertEqual(code, 1, name)
            self.assertIn(f"id must look like {prefix}-1", out)
            path.write_text(original, encoding="utf-8")

    def test_starter_files_validate_once_copied(self):
        empty_dir = Path(tempfile.mkdtemp()) / "demo"
        empty_dir.mkdir()
        try:
            self.assertEqual(run_setup(empty_dir, "--name", "Demo")[0], 0)
            for f in ("requirements", "tests", "environments", "permissions"):
                shutil.copy(pc.SKILL / "assets/starter/optional-registers" / f"{f}.yaml", empty_dir / "pmo/registers" / f"{f}.yaml")
            code, out, _ = run_render(empty_dir)
            self.assertEqual(code, 0, out)
            code, out, _ = run_render(empty_dir, "--check")
            self.assertEqual(code, 0, out)
        finally:
            shutil.rmtree(empty_dir.parent)

    def test_permission_role_must_be_in_domain_roles(self):
        self.append("permissions", '  - {id: PERM-99, resource: Profile, action: delete, roles: [owner], condition: "", source: src/auth.js, notes: "", origin: stated}')
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 1)
        self.assertIn("roles 'owner' not in", out)

        # domain.roles: [] accepts any value
        self.write_config({"domain": {"roles": []}})
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)

    def test_test_links_must_exist(self):
        # task: T-99 fails
        tests_path = self.reg / "tests.yaml"
        original = tests_path.read_text(encoding="utf-8")

        self.append("tests", '  - {id: TST-99, title: Bad task, kind: acceptance, requirement: null, task: T-99, issue: null, expected: ok, status: passed, run_on: 2026-03-06, owner: alice, evidence: "", notes: "", origin: stated}')
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 1)
        self.assertIn("task 'T-99' is not an id in tasks", out)

        # requirement: REQ-9 fails
        tests_path.write_text(original, encoding="utf-8")
        self.append("tests", '  - {id: TST-99, title: Bad req, kind: acceptance, requirement: REQ-9, task: null, issue: null, expected: ok, status: passed, run_on: 2026-03-06, owner: alice, evidence: "", notes: "", origin: stated}')
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 1)
        self.assertIn("requirement 'REQ-9' is not an id in requirements", out)

        # issue: I-9 fails
        tests_path.write_text(original, encoding="utf-8")
        self.append("tests", '  - {id: TST-99, title: Bad issue, kind: acceptance, requirement: null, task: null, issue: I-9, expected: ok, status: passed, run_on: 2026-03-06, owner: alice, evidence: "", notes: "", origin: stated}')
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 1)
        self.assertIn("issue 'I-9' is not an id in issues", out)

    def test_task_tests_field_is_checked(self):
        tasks_path = self.reg / "tasks.yaml"
        original = tasks_path.read_text(encoding="utf-8")

        # tests: [TST-9] fails
        self.append("tasks", '  - {id: T-99, title: Bad test ref, team: platform, group: infra, priority: low, owner: alice, status: not-started, due: 2026-03-20, period: 2026-03, notes: "", tests: [TST-9]}')
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 1)
        self.assertIn("tests 'TST-9' is not an id in tests", out)

        # tests: [TST-1] passes
        tasks_path.write_text(original, encoding="utf-8")
        self.append("tasks", '  - {id: T-99, title: Good test ref, team: platform, group: infra, priority: low, owner: alice, status: not-started, due: 2026-03-20, period: 2026-03, notes: "", tests: [TST-1]}')
        code, out, _ = run_render(self.root)
        self.assertEqual(code, 0, out)

    def test_setup_does_not_create_the_four_registers(self):
        empty_dir = Path(tempfile.mkdtemp()) / "demo"
        empty_dir.mkdir()
        try:
            code, out, err = run_setup(empty_dir, "--name", "Demo")
            self.assertEqual(code, 0, err)
            reg_dir = empty_dir / "pmo/registers"
            for f in ("requirements.yaml", "tests.yaml", "environments.yaml", "permissions.yaml"):
                self.assertFalse((reg_dir / f).exists(), f"{f} should not be created by setup")
            code, out, _ = run_render(empty_dir, "--check")
            self.assertEqual(code, 0, out)
        finally:
            shutil.rmtree(empty_dir.parent)

    def test_project_without_the_new_files_still_validates(self):
        for f in ("requirements.yaml", "tests.yaml", "environments.yaml", "permissions.yaml"):
            p = self.reg / f
            if p.exists():
                p.unlink()
        for v in ("requirements.md", "tests.md", "environments.md", "permissions.md"):
            p = self.views / v
            if p.exists():
                p.unlink()
        tasks_file = self.reg / "tasks.yaml"
        text = tasks_file.read_text(encoding="utf-8")
        text = text.replace(", tests: [TST-1]", "")
        tasks_file.write_text(text, encoding="utf-8")
        tasks_view = self.views / "tasks.md"
        if tasks_view.exists():
            vtext = tasks_view.read_text(encoding="utf-8")
            vtext = vtext.replace("\n\n**Done without a linked test:** none", "")
            tasks_view.write_text(vtext, encoding="utf-8")
        code, out, _ = run_render(self.root, "--check")
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
