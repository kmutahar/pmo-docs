# Tests dev/scrub.sh and .githooks/commit-msg in a throwaway git repo.
# Run from the repo root: python3 -m unittest tests.test_scrub
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ScrubTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.git("init", "-q")
        (self.tmp / "dev").mkdir()
        shutil.copy(ROOT / "dev/scrub.sh", self.tmp / "dev/scrub.sh")
        (self.tmp / ".scrub-names").write_text("acmecorp\n", encoding="utf-8")
        (self.tmp / ".gitignore").write_text(".scrub-names\ntmp/\n", encoding="utf-8")

    def git(self, *args):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.t"}
        return subprocess.run(["git", *args], cwd=self.tmp, env=env,
                              capture_output=True, text=True)

    def scrub(self, **env):
        # drop CI so the local behaviour is tested even when this suite runs in CI
        env = {**{k: v for k, v in os.environ.items() if k != "CI"}, **env}
        return subprocess.run(["bash", "dev/scrub.sh"], cwd=self.tmp, env=env,
                              capture_output=True, text=True)

    def write(self, name, text):
        p = self.tmp / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_clean_repo_passes(self):
        self.write("a.md", "nothing private\n")
        self.assertEqual(self.scrub().returncode, 0)

    def test_untracked_name_fails(self):
        self.write("a.md", "built for AcmeCorp\n")
        self.assertEqual(self.scrub().returncode, 1)

    def test_staged_leak_fixed_only_on_disk_still_fails(self):
        self.write("a.md", "built for acmecorp\n")
        self.git("add", "a.md")
        self.write("a.md", "clean now\n")  # not re-staged: the commit would still leak
        self.assertEqual(self.scrub().returncode, 1)

    def test_generic_patterns_fail(self):
        # built in pieces so this file does not trip the real repo's scrub
        for text in ("see /ho" "me/someone/x\n", "mail a.b" "@example.org\n", "call +" "966 55 123 4567\n"):
            self.write("a.md", text)
            self.assertEqual(self.scrub().returncode, 1, text)

    def test_missing_names_fails_locally_but_not_in_ci(self):
        (self.tmp / ".scrub-names").unlink()
        self.write("a.md", "nothing private\n")
        self.assertEqual(self.scrub().returncode, 1)
        self.assertEqual(self.scrub(CI="true").returncode, 0)

    def test_gitignored_workspace_is_skipped(self):
        self.write("tmp/source/raw.md", "acmecorp internals\n")
        self.assertEqual(self.scrub().returncode, 0)

    def test_commit_msg_hook(self):
        hook = ROOT / ".githooks/commit-msg"
        msg = self.tmp / "MSG"
        run = lambda: subprocess.run(["bash", str(hook), str(msg)], cwd=self.tmp).returncode
        msg.write_text("feat: add render\n# On branch acmecorp-x\n", encoding="utf-8")
        self.assertEqual(run(), 0)  # git comment lines are ignored
        msg.write_text("feat: add acmecorp render\n", encoding="utf-8")
        self.assertEqual(run(), 1)


if __name__ == "__main__":
    unittest.main()
