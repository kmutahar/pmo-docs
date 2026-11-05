# Tests dev/release (--help, version and tag checks, dirty tree, dry run, the non-dry path up to the first prompt, with stub git-cliff/claude) in a throwaway git repo.
# Run from the repo root: python3 -m unittest tests.test_release
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for rel in ("dev/release", "skills/pmo-docs/SKILL.md", ".claude-plugin/plugin.json"):
            (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.tmp / rel)
        self.git("init", "-q", "-b", "main")
        self.git("add", ".")
        self.git("commit", "-qm", "init")

    def git(self, *args, check=True):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.t"}
        r = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                           cwd=self.tmp, env=env, capture_output=True, text=True)
        if check:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def release(self, *args, **env):
        # no terminal and no stdin: a prompt could only read EOF, which counts as No
        env = {**{k: v for k, v in os.environ.items() if k not in ("DRY_RUN", "RELEASE_SKIP_CHECKS")},
               "RELEASE_SKIP_CHECKS": "1", **env}
        return subprocess.run(["bash", "dev/release", *args], cwd=self.tmp, env=env, text=True,
                              capture_output=True, stdin=subprocess.DEVNULL, start_new_session=True)

    def test_help(self):
        r = self.release("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Usage: dev/release", r.stdout)

    def test_needs_a_version(self):
        self.assertEqual(self.release().returncode, 1)

    def test_bad_version_rejected(self):
        for v in ("1.2", "x.y.z", "1.2.3.4", "vv1.2.3", "1.2.3-rc.1", "01.2.3"):
            r = self.release("--dry-run", v)
            self.assertEqual(r.returncode, 1, v)
            self.assertIn("not a semantic version", r.stderr)

    def test_existing_tag_rejected(self):
        self.git("tag", "v9.9.9")
        r = self.release("--dry-run", "9.9.9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)

    def test_dirty_tree_rejected_but_memory_md_ignored(self):
        (self.tmp / "memory.md").write_text("local\n", encoding="utf-8")
        self.assertEqual(self.release("--dry-run", "9.9.9").returncode, 0)
        (self.tmp / "notes.txt").write_text("x\n", encoding="utf-8")
        r = self.release("--dry-run", "9.9.9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("notes.txt", r.stderr)
        self.assertNotIn("memory.md", r.stderr.split("uncommitted")[0])
        self.assertEqual(self.release("--dry-run", "--allow-dirty", "v9.9.9").returncode, 0)

    def test_dirty_version_file_refused_even_with_allow_dirty(self):
        with open(self.tmp / ".claude-plugin/plugin.json", "a", encoding="utf-8") as f:
            f.write("\n")
        self.assertEqual(self.release("--dry-run", "--allow-dirty", "9.9.9").returncode, 1)

    def test_dry_run_changes_nothing_and_never_asks(self):
        r = self.release("--dry-run", "v9.9.9", DRY_RUN="")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nothing changed", r.stdout)
        self.assertNotIn("[y/N]", r.stderr + r.stdout)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertFalse((self.tmp / "CHANGELOG.md").exists())

    def test_unexpected_skill_structure_fails(self):
        skill = self.tmp / "skills/pmo-docs/SKILL.md"
        skill.write_text("---\nname: x\n---\n", encoding="utf-8")
        self.git("commit", "-qam", "break")
        r = self.release("--dry-run", "9.9.9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("metadata", r.stderr)

    def test_bad_dry_run_env_rejected(self):
        r = self.release("9.9.9", DRY_RUN="yes")
        self.assertEqual(r.returncode, 1)
        self.assertIn("DRY_RUN", r.stderr)

    def stub_non_dry(self):
        """Stub git-cliff, claude, scrub and one test so the real path runs without a terminal."""
        bin_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, bin_dir)
        (bin_dir / "git-cliff").write_text(
            '#!/bin/sh\nif [ "$1" = "-o" ]; then echo "# Changelog" > "$2"; else echo "notes"; fi\n', encoding="utf-8")
        (bin_dir / "claude").write_text('#!/bin/sh\necho "warning: stub"\n', encoding="utf-8")
        for f in bin_dir.iterdir():
            f.chmod(0o755)
        (self.tmp / "dev/scrub.sh").write_text("exit 0\n", encoding="utf-8")
        (self.tmp / "tests").mkdir()
        (self.tmp / "tests/test_stub.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        pass\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "stubs")
        return {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}

    def test_non_dry_run_writes_version_then_aborts_without_a_terminal(self):
        env = self.stub_non_dry()
        before = self.git("rev-parse", "HEAD").stdout
        r = self.release("9.9.9", **env)  # no tty: the first prompt counts as No
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("Aborted.", r.stderr)
        self.assertIn("To undo:", r.stderr)
        self.assertIn("rm -f CHANGELOG.md", r.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, before)
        self.assertEqual(self.git("tag").stdout, "")
        # the version writer changed both files and nothing else in them
        skill = (self.tmp / "skills/pmo-docs/SKILL.md").read_text(encoding="utf-8")
        self.assertIn('metadata:\n  version: "9.9.9"\n', skill)
        self.assertEqual(json.loads((self.tmp / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"], "9.9.9")
        self.assertEqual((self.tmp / "CHANGELOG.md").read_text(encoding="utf-8"), "# Changelog\n")
        diff = self.git("diff", "--numstat").stdout.split()
        self.assertEqual(diff[0::3], ["1", "1"], diff)  # one line added in each file
        self.assertEqual(diff[1::3], ["1", "1"], diff)

    def test_changelog_links_without_owner_repo_stop_the_release(self):
        env = self.stub_non_dry()
        (Path(env["PATH"].split(os.pathsep)[0]) / "git-cliff").write_text(
            '#!/bin/sh\nif [ "$1" = "-o" ]; then echo "https://github.com///commit/x" > "$2"; else echo notes; fi\n', encoding="utf-8")
        r = self.release("9.9.9", **env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no owner/repo", r.stderr)

    def test_failing_validate_stops_the_release(self):
        env = self.stub_non_dry()
        (Path(env["PATH"].split(os.pathsep)[0]) / "claude").write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
        r = self.release("9.9.9", **env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("plugin validation failed", r.stderr)
        self.assertFalse((self.tmp / "CHANGELOG.md").exists())


if __name__ == "__main__":
    unittest.main()
