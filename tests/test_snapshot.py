"""Tests for scripts/snapshot.py and `where.py --delta` on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_snapshot"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"


def run(tool, project, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / tool), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.tasks = self.root / "pmo/registers/tasks.yaml"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_writes_hashes_and_ids_with_statuses_only(self):
        code, out, _ = run("snapshot.py", self.root, "--as-of", "2026-03-01")
        self.assertEqual((code, out.strip()), (0, "pmo/snapshots/2026-03-01.json"))
        text = (self.root / out.strip()).read_text(encoding="utf-8")
        snap = json.loads(text)
        self.assertEqual(snap["entries"]["tasks"]["T-001"], "in-progress")
        self.assertEqual(snap["entries"]["tasks"]["T-003"], "done")
        self.assertEqual(set(snap["entries"]), {"tasks", "risks", "issues", "actions"})
        self.assertIn("tasks", snap["hashes"])
        self.assertEqual(len(snap["hashes"]["tasks"]), 8)
        for secret in ("Set up staging server", "Overdue on purpose", "alice"):  # no free text, no titles
            self.assertNotIn(secret, text)

    def test_path_is_configurable(self):
        cfg = self.root / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8") + "\npaths:\n  snapshots: pmo/snaps\n", encoding="utf-8")
        code, out, _ = run("snapshot.py", self.root, "--as-of", "2026-03-01")
        self.assertEqual((code, out.strip()), (0, "pmo/snaps/2026-03-01.json"))
        self.assertTrue((self.root / "pmo/snaps/2026-03-01.json").is_file())

    def test_path_must_stay_inside_the_project(self):
        cfg = self.root / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8") + "\npaths:\n  snapshots: ../out\n", encoding="utf-8")
        code, _, err = run("snapshot.py", self.root)
        self.assertEqual(code, 2)
        self.assertIn("paths.snapshots", err)

    def test_delta_without_a_snapshot(self):
        code, out, _ = run("where.py", self.root, "--delta")
        self.assertEqual((code, out.strip()), (0, "delta: no snapshot"))

    def test_delta_ignores_a_snapshot_of_the_same_day_or_later(self):
        run("snapshot.py", self.root, "--as-of", "2026-03-10")
        _, out, _ = run("where.py", self.root, "--delta", "--as-of", "2026-03-10")
        self.assertEqual(out.strip(), "delta: no snapshot")

    def test_delta_lists_changed_added_and_removed(self):
        run("snapshot.py", self.root, "--as-of", "2026-03-01")
        text = self.tasks.read_text(encoding="utf-8")
        text = text.replace("owner: alice, status: in-progress", "owner: alice, status: done")  # T-001 changes
        text = "\n".join(l for l in text.splitlines() if "{id: T-002," not in l) + "\n"  # T-002 removed
        text += "  - {id: T-009, title: New, owner: bob, status: not-started}\n"  # T-009 added
        self.tasks.write_text(text, encoding="utf-8")
        code, out, _ = run("where.py", self.root, "--delta", "--as-of", "2026-03-08")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "delta: since 2026-03-01",
            "changed_tasks: T-001 in-progress->done",
            "added_tasks: T-009 not-started",
            "removed_tasks: T-002 not-started",
        ])

    def test_delta_uses_the_latest_earlier_snapshot(self):
        run("snapshot.py", self.root, "--as-of", "2026-03-01")
        self.tasks.write_text(self.tasks.read_text(encoding="utf-8").replace("owner: alice, status: in-progress", "owner: alice, status: done"), encoding="utf-8")
        run("snapshot.py", self.root, "--as-of", "2026-03-05")
        _, out, _ = run("where.py", self.root, "--delta", "--as-of", "2026-03-08")
        self.assertEqual(out.splitlines(), ["delta: since 2026-03-05"])

    def test_where_without_type_or_delta_is_a_usage_error(self):
        code, _, err = run("where.py", self.root)
        self.assertEqual(code, 2)
        self.assertIn("type", err)

    def test_delta_reports_corrupt_snapshot_cleanly(self):
        snaps = self.root / "pmo/snapshots"
        snaps.mkdir(parents=True, exist_ok=True)
        (snaps / "2026-03-01.json").write_text("{not json", encoding="utf-8")
        code, _, err = run("where.py", self.root, "--delta", "--as-of", "2026-03-08")
        self.assertEqual(code, 2)
        self.assertIn("corrupt snapshot", err)

        (snaps / "2026-03-01.json").write_text('{"date": "2026-03-01"}\n', encoding="utf-8")
        code, _, err = run("where.py", self.root, "--delta", "--as-of", "2026-03-08")
        self.assertEqual(code, 2)
        self.assertIn("corrupt snapshot", err)

        (snaps / "2026-03-01.json").write_text('{"entries": {"tasks": ["T-001"]}}\n', encoding="utf-8")
        code, _, err = run("where.py", self.root, "--delta", "--as-of", "2026-03-08")
        self.assertEqual(code, 2)
        self.assertIn("corrupt snapshot", err)


if __name__ == "__main__":
    unittest.main()
