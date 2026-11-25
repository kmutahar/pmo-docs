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

# Stub for dev/run-evals: writes aggregate-result.json per case from STUB.json
# ({case: pass|fail|limit|error|[...]}, default pass) and logs each call's cases to calls.log.
STUB = r'''
import json, sys
from pathlib import Path
a = sys.argv[1:]
cases = [a[i + 1] for i, x in enumerate(a) if x == "--case"]
out = Path(a[a.index("--out") + 1])
here = Path(__file__).parent
plan = json.loads((here / "STUB.json").read_text()) if (here / "STUB.json").exists() else {}
log = here / "calls.log"
prev = log.read_text().splitlines() if log.exists() else []
with open(log, "a") as f:
    f.write(" ".join(cases) + "\n")
for c in cases:
    d = out / "cases" / c
    d.mkdir(parents=True, exist_ok=True)
    spec = plan.get(c, "pass")
    if isinstance(spec, list):
        idx = sum(1 for line in prev if c in line.split())
        kind = spec[idx] if idx < len(spec) else spec[-1]
    else:
        kind = spec
    err = None
    if kind == "limit":
        err = "exit 1: You've hit your 5-hour limit"
    elif kind == "error":
        err = "runner crashed"
    run = {"passed": kind == "pass", "error": err, "graders": []}
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

    def sync(self, *args, jobs=2):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), "--jobs", str(jobs),
                               "--runner", f"{sys.executable} {self.root / 'stub.py'}", *args],
                              capture_output=True, text=True)

    def add_case(self, name):
        (self.root / "evals" / name).mkdir(parents=True, exist_ok=True)
        (self.root / "evals" / name / "prompt.md").write_text(name)

    def set_status(self, statuses):
        self.sync("--plan")
        lines = (self.root / ".eval-runs" / "status.md").read_text().splitlines()
        out = lines[:2]
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            c = cells[0]
            if c in statuses:
                status, runs_done, runs_needed, passes = statuses[c]
                cells[1:5] = [status, str(runs_done), str(runs_needed), str(passes)]
            out.append("| " + " | ".join(cells) + " |")
        (self.root / ".eval-runs" / "status.md").write_text("\n".join(out) + "\n")

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
        r = self.sync()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.calls(), ["a b", "c", "a"])
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

    def test_priority_order_in_plan_and_batches(self):
        self.add_case("d")
        (self.root / "dev" / "eval-runs-needed.txt").write_text("c 2\n")
        self.set_status({
            "a": ("fail", 1, 1, 0),
            "b": ("stale", 0, 1, 0),
            "c": ("partial", 1, 2, 1),
            "d": ("not-run", 0, 1, 0),
        })
        plan = self.sync("--plan", jobs=4)
        planned = [line.split()[0] for line in plan.stdout.splitlines() if line.startswith("  ") and not line.startswith("  retest")]
        self.assertEqual(planned, ["d", "c", "b", "a"])
        r = self.sync(jobs=4)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.calls(), ["d", "c", "b", "a"])

    def test_stale_multirun_finishes_partial_before_fail(self):
        (self.root / "dev" / "eval-runs-needed.txt").write_text("b 2\n")
        self.set_status({
            "a": ("fail", 1, 1, 0),
            "b": ("stale", 0, 2, 0),
            "c": ("pass", 1, 1, 1),
        })
        r = self.sync(jobs=4)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.calls(), ["b", "b", "a"])
        self.assertEqual(self.table()["b"][1:5], ["pass", "2", "2", "2"])

    def test_fail_orders_fewest_runs_done_first(self):
        self.set_status({
            "a": ("fail", 3, 1, 0),
            "b": ("fail", 1, 1, 0),
            "c": ("fail", 1, 1, 0),
        })
        plan = self.sync("--plan", jobs=1)
        planned = [line.split()[0] for line in plan.stdout.splitlines() if line.startswith("  ") and not line.startswith("  retest")]
        self.assertEqual(planned, ["b", "c", "a"])
        r = self.sync(jobs=1)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.calls(), ["b", "c", "a"])

    def test_fresh_not_run_failure_does_not_retry_in_same_call(self):
        self.stub(a="fail", b="pass", c="pass")
        r = self.sync(jobs=4)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.calls(), ["a b c"])
        self.assertEqual(self.table()["a"][1:5], ["fail", "1", "1", "0"])

    def test_quota_limit_mid_partial_resumes_partial_first(self):
        (self.root / "dev" / "eval-runs-needed.txt").write_text("b 2\n")
        self.set_status({
            "a": ("fail", 1, 1, 0),
            "b": ("not-run", 0, 2, 0),
            "c": ("stale", 0, 1, 0),
        })
        self.stub(b=["pass", "limit"], a="pass", c="pass")
        r = self.sync(jobs=4)
        self.assertIn("usage limit", r.stdout)
        self.assertEqual(self.calls(), ["b", "b"])
        self.assertEqual(self.table()["b"][1:5], ["partial", "1", "2", "1"])

        self.stub(a="pass", b="pass", c="pass")
        r2 = self.sync(jobs=4)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(self.calls()[2:], ["b", "c", "a"])

    def test_non_quota_error_does_not_loop(self):
        self.stub(a="error", b="pass", c="pass")
        r = self.sync(jobs=4)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.calls(), ["a b c"])
        self.assertEqual(self.table()["a"][1:5], ["not-run", "0", "1", "0"])


if __name__ == "__main__":
    unittest.main()
