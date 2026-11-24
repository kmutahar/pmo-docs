"""dev/eval-sync on a temp repo with a stub runner: first-run table, skipping done cases, re-running failures,
stale case folders, runs_needed, the usage-limit stop and --import. Nothing real runs.
Run: python3 -m unittest tests.test_eval_sync"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "dev" / "eval-sync"

# Stub for dev/run-evals: writes aggregate-result.json per case from STUB.json ({case: pass|fail|limit}, default pass)
# and logs each call's cases to calls.log.
STUB = r'''
import json, sys
from pathlib import Path
a = sys.argv[1:]
cases = [a[i + 1] for i, x in enumerate(a) if x == "--case"]
out = Path(a[a.index("--out") + 1])
here = Path(__file__).parent
plan = json.loads((here / "STUB.json").read_text()) if (here / "STUB.json").exists() else {}
with open(here / "calls.log", "a") as f:
    f.write(" ".join(cases) + "\n")
for c in cases:
    d = out / "cases" / c
    d.mkdir(parents=True, exist_ok=True)
    kind = plan.get(c, "pass")
    run = {"passed": kind == "pass", "error": "exit 1: You've hit your 5-hour limit" if kind == "limit" else None, "graders": []}
    (d / "aggregate-result.json").write_text(json.dumps({"cases": [{"arms": {"with": [run]}}]}))
'''


class EvalSync(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = Path(self._t.name)
        for c in ("a", "b", "c"):
            (self.root / "evals" / c).mkdir(parents=True)
            (self.root / "evals" / c / "prompt.md").write_text(c)
        (self.root / "skills" / "pmo-docs").mkdir(parents=True)
        (self.root / "skills" / "pmo-docs" / "SKILL.md").write_text("v1")
        (self.root / "dev").mkdir()
        (self.root / "stub.py").write_text(STUB)

    def stub(self, **plan):
        (self.root / "STUB.json").write_text(json.dumps(plan))

    def sync(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), "--jobs", "2",
                               "--runner", f"{sys.executable} {self.root / 'stub.py'}", *args],
                              capture_output=True, text=True)

    def table(self):
        rows = {}
        for line in (self.root / ".eval-runs" / "status.md").read_text().splitlines()[2:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows[cells[0]] = cells
        return rows

    def calls(self):
        p = self.root / "calls.log"
        return p.read_text().splitlines() if p.exists() else []

    def test_first_run_creates_table_and_runs_each_case_once(self):
        r = self.sync()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual({c: v[1] for c, v in self.table().items()}, {"a": "pass", "b": "pass", "c": "pass"})
        self.assertEqual(sorted(w for line in self.calls() for w in line.split()), ["a", "b", "c"])

    def test_all_passed_runs_nothing(self):
        self.sync()
        n = len(self.calls())
        r = self.sync()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(self.calls()), n)

    def test_only_failures_rerun(self):
        self.stub(b="fail")
        self.assertEqual(self.sync().returncode, 1)
        self.stub()
        self.sync()
        self.assertEqual(self.calls()[-1], "b")
        self.assertEqual(self.table()["b"][1], "pass")

    def test_runs_needed_takes_two_passes(self):
        (self.root / "dev" / "eval-runs-needed.txt").write_text("a 2\n")
        self.sync()
        self.assertEqual(self.table()["a"][1:5], ["partial", "1", "2", "1"])
        self.sync()
        self.assertEqual(self.calls()[-1], "a")
        self.assertEqual(self.table()["a"][1:5], ["pass", "2", "2", "2"])

    def test_changed_case_folder_goes_stale_and_reruns_alone(self):
        self.sync()
        (self.root / "evals" / "c" / "prompt.md").write_text("changed")
        self.sync()
        self.assertEqual(self.calls()[-1], "c")

    def test_skill_change_warns_and_stale_marks(self):
        self.sync()
        (self.root / "skills" / "pmo-docs" / "SKILL.md").write_text("v2")
        r = self.sync("--plan")
        self.assertIn("older skill version", r.stdout)
        n = len(self.calls())
        self.sync("--stale", "b")
        self.assertEqual(len(self.calls()), n + 1)
        self.assertEqual(self.calls()[-1], "b")

    def test_new_case_is_picked_up(self):
        self.sync()
        (self.root / "evals" / "d").mkdir()
        (self.root / "evals" / "d" / "prompt.md").write_text("d")
        self.sync()
        self.assertEqual(self.calls()[-1], "d")

    def test_usage_limit_stops_and_leaves_not_run(self):
        self.stub(a="limit")
        r = self.sync()
        self.assertIn("usage limit", r.stdout)
        t = self.table()
        self.assertEqual(t["a"][1], "not-run")
        self.assertEqual(t["c"][1], "not-run")
        self.assertEqual(len(self.calls()), 1)  # batch 2 (case c) never started

    def test_plan_runs_nothing_and_force_runs_done_case(self):
        self.sync()
        n = len(self.calls())
        self.sync("--plan", "--force-all")
        self.assertEqual(len(self.calls()), n)
        self.sync("--force", "a")
        self.assertEqual(self.calls()[-1], "a")

    def test_import_records_old_run_only_when_case_unchanged(self):
        old = self.root / "old"
        for c in ("a", "b"):
            (old / "plugin" / "evals" / c).mkdir(parents=True)
            (old / "plugin" / "evals" / c / "prompt.md").write_text(c)
            d = old / "cases" / c
            d.mkdir(parents=True, exist_ok=True)
            (d / "aggregate-result.json").write_text(json.dumps({"cases": [{"arms": {"with": [{"passed": c == "a", "error": None, "graders": []}]}}]}))
        (old / "plugin" / "SKILL.md").write_text("v1")
        (old / "plugin" / "evals" / "b" / "prompt.md").write_text("old b")  # b changed since that run
        r = self.sync("--import", str(old))
        self.assertIn("imported 1", r.stdout)
        self.assertEqual(self.table()["a"][1], "pass")
        self.assertEqual(self.table()["b"][1], "not-run")


if __name__ == "__main__":
    unittest.main()
