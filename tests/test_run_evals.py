"""dev/run-evals with a fake `claude` on PATH: the run folder layout, kept sandboxes moved in, summary and exit code.
Run: python3 -m unittest tests.test_run_evals"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Fakes `claude plugin eval`: records its arguments, leaves a sealed kept sandbox in $TMPDIR like the real CLI,
# prints the CLI's log lines, and fails the case named done-needs-qa.
FAKE = r"""#!/usr/bin/env bash
set -euo pipefail
case=""; outdir=""; args=("$@")
while [ $# -gt 0 ]; do
  case "$1" in --case) case="$2"; shift 2 ;; --output-dir) outdir="$2"; shift 2 ;; *) shift ;; esac
done
printf '%s\n' "${args[@]}" > "$outdir/args.txt"
pwd > "$outdir/cwd.txt"
k="$(mktemp -d "$TMPDIR/claude-eval-XXXXXX")"
mkdir -p "$k/out" "$k/sealed/proj/cwd"; echo '{}' > "$k/out/trace.jsonl"; echo draft > "$k/sealed/proj/cwd/file.md"
chmod 000 "$k/sealed/proj" "$k/sealed"; chmod 500 "$k"
echo "  kept temp: $k"
echo '{"cases": []}' > "$outdir/aggregate-result.json"
if [ "$case" = done-needs-qa ]; then
  echo "    ✗ asks-for-qa (weight 2): judge votes: FAIL FAIL FAIL"
  echo "✗ $case  score 0.60  (1 run)  \$0.20"; exit 1
fi
echo "    ✓ skill-fired (weight 1): Skill called 1x"
echo "✓ $case  score 1.00  (1 run)  \$0.10"
"""


class RunEvals(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(self._cleanup)
        (self.tmp / "bin").mkdir()
        (self.tmp / "t").mkdir()
        fake = self.tmp / "bin/claude"
        fake.write_text(FAKE, encoding="utf-8")
        fake.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.tmp / 'bin'}:{os.environ['PATH']}", TMPDIR=str(self.tmp / "t"),
                        HOME=str(self.tmp / "home"))

    def _cleanup(self):
        subprocess.run(["chmod", "-R", "u+rwX", str(self.tmp)], check=False)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_evals(self, *args):
        return subprocess.run(["bash", str(REPO / "dev/run-evals"), *args], env=self.env,
                              capture_output=True, text=True, timeout=120)

    def test_keeps_everything_in_one_run_folder(self):
        out = self.tmp / "run"
        p = self.run_evals("--case", "ask-dont-guess", "--case", "done-needs-qa", "--jobs", "2", "--out", str(out))
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)  # one case failed
        self.assertTrue((out / "plugin/SKILL.md").exists())
        self.assertTrue((out / "plugin/evals/ask-dont-guess/prompt.md").exists())
        self.assertTrue((out / "plugin/examples/acme/pmo/config.yaml").exists())
        for c in ("ask-dont-guess", "done-needs-qa"):
            d = out / "cases" / c
            self.assertTrue((d / "eval.log").exists(), c)
            self.assertTrue((d / "aggregate-result.json").exists(), c)
            self.assertEqual((d / "sandbox-1/sealed/proj/cwd/file.md").read_text(encoding="utf-8"), "draft\n", c)
            self.assertTrue((d / "sandbox-1/out/trace.jsonl").exists(), c)
            self.assertEqual((d / "cwd.txt").read_text(encoding="utf-8").strip(), str(out / "plugin"), c)
        self.assertEqual(list((self.tmp / "t").iterdir()), [], "kept sandboxes left in TMPDIR")
        args = (out / "cases/ask-dont-guess/args.txt").read_text(encoding="utf-8").split("\n")
        for flag in ("--keep-temp", "--scaffold", "--trust-plugin"):
            self.assertIn(flag, args)
        self.assertEqual(args[args.index("--model") + 1], "sonnet")
        self.assertEqual(args[args.index("--judge-model") + 1], "sonnet")
        self.assertEqual(args[args.index("--report") + 1], str(out / "cases/ask-dont-guess/report.html"))
        summary = (out / "summary.log").read_text(encoding="utf-8")
        self.assertIn("✓ ask-dont-guess", summary)
        self.assertRegex(summary, r"✗ done-needs-qa .*failed: asks-for-qa")
        self.assertIn("total: 1/2 passed, $0.30", summary)
        self.assertIn("start  ask-dont-guess", p.stdout)
        self.assertIn("/2]", p.stdout)

    def test_all_pass_exits_zero_and_passes_extra_options(self):
        out = self.tmp / "run"
        p = self.run_evals("--case", "ask-dont-guess", "--runs", "2", "--out", str(out), "--", "--max-cost-usd", "1")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        args = (out / "cases/ask-dont-guess/args.txt").read_text(encoding="utf-8").split("\n")
        self.assertEqual(args[args.index("--runs") + 1], "2")
        self.assertEqual(args[args.index("--max-cost-usd") + 1], "1")

    def test_default_out_is_in_home(self):
        p = self.run_evals("--case", "ask-dont-guess")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        runs = list((self.tmp / "home/pmo-eval-runs").iterdir())
        self.assertEqual(len(runs), 1)
        self.assertRegex(runs[0].name, r"^\d{8}T\d{6}Z$")

    def test_usage_errors(self):
        self.assertEqual(self.run_evals("--case", "no-such-case", "--out", str(self.tmp / "x")).returncode, 2)
        self.assertEqual(self.run_evals("--bogus").returncode, 2)
        self.assertEqual(self.run_evals("--help").returncode, 0)


if __name__ == "__main__":
    unittest.main()
