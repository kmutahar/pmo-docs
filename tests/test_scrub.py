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

    def _git_env(self, **extra):
        return {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t.t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t.t",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            **extra,
        }

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.tmp, env=self._git_env(),
                              capture_output=True, text=True, encoding="utf-8")

    def scrub(self, *args, **env):
        # drop CI so the local behaviour is tested even when this suite runs in CI
        base = {k: v for k, v in self._git_env().items() if k != "CI"}
        return subprocess.run(["bash", "dev/scrub.sh", *args], cwd=self.tmp, env={**base, **env},
                              capture_output=True, text=True, encoding="utf-8")

    def hook(self, msg):
        hook = ROOT / ".githooks/commit-msg"
        return subprocess.run(["bash", str(hook), str(msg)], cwd=self.tmp, env=self._git_env(),
                              capture_output=True, text=True, encoding="utf-8")

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
        for text in ("see /ho" "me/someone/x\n", "mail a.b" "@example.org\n", "call +" "1 555 010 0199\n"):
            self.write("a.md", text)
            self.assertEqual(self.scrub().returncode, 1, text)

    def test_macos_users_path_fails(self):
        self.write("a.md", "see /Us" "ers/x\n")
        self.assertEqual(self.scrub().returncode, 1)

    def test_windows_users_path_fails(self):
        self.write("a.md", "see C:\\Us" "ers\\x\n")
        self.assertEqual(self.scrub().returncode, 1)

    def test_dashed_phone_fails(self):
        self.write("a.md", "call +" "1-555-010-0199\n")
        self.assertEqual(self.scrub().returncode, 1)

    def test_bracketed_phone_fails(self):
        self.write("a.md", "call +" "1 (555) 010-0199\n")
        self.assertEqual(self.scrub().returncode, 1)

    def test_tilde_path_is_allowed(self):
        self.write("a.md", "see ~/project/notes.md\n")
        self.assertEqual(self.scrub().returncode, 0)

    def test_missing_names_fails_locally_but_not_in_ci(self):
        (self.tmp / ".scrub-names").unlink()
        self.write("a.md", "nothing private\n")
        self.assertEqual(self.scrub().returncode, 1)
        self.assertEqual(self.scrub(CI="true").returncode, 0)

    def test_gitignored_workspace_is_skipped(self):
        self.write("tmp/source/raw.md", "acmecorp internals\n")
        self.assertEqual(self.scrub().returncode, 0)

    def test_commit_msg_hook(self):
        msg = self.tmp / "MSG"
        msg.write_text("feat: add render\n# On branch acmecorp-x\n", encoding="utf-8")
        self.assertEqual(self.hook(msg).returncode, 0)  # git comment lines are ignored
        msg.write_text("feat: add acmecorp render\n", encoding="utf-8")
        self.assertEqual(self.hook(msg).returncode, 1)

    def test_commit_msg_hook_blocks_generic_patterns(self):
        msg = self.tmp / "MSG"
        msg.write_text("docs: clean\n# email a.b" "@example.org\n", encoding="utf-8")
        self.assertEqual(self.hook(msg).returncode, 0)
        for text in (
            "docs: from a.b" "@example.org\n",
            "docs: at /Us" "ers/x\n",
            "docs: at C:\\Us" "ers\\x\n",
            "docs: call +" "1-555-010-0199\n",
        ):
            msg.write_text(text, encoding="utf-8")
            self.assertEqual(self.hook(msg).returncode, 1, text)

    def test_invalid_name_pattern_is_an_error_not_clean(self):
        (self.tmp / ".scrub-names").write_text("acme(\n", encoding="utf-8")
        self.write("a.md", "nothing private\n")
        self.assertEqual(self.scrub().returncode, 1)
        msg = self.tmp / "MSG"
        msg.write_text("feat: add render\n", encoding="utf-8")
        self.assertEqual(self.hook(msg).returncode, 1)

    def test_binary_files_are_scanned_for_text_matches(self):
        bin_path = self.tmp / "a.bin"
        bin_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x01\x02")
        self.assertEqual(self.scrub().returncode, 0)
        self.assertEqual(self.git("add", "a.bin").returncode, 0)
        self.assertEqual(self.scrub().returncode, 0)

        bad_bin = self.tmp / "b.bin"
        bad_bin.write_bytes(b"\x00\x01acmecorp\x00\n")
        res = self.scrub()
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stderr, "")
        bad_bin.unlink()

        bin_path.write_bytes(b"\x00\x01/Us" + b"ers/x\x00\n")
        self.assertEqual(self.git("add", "a.bin").returncode, 0)
        res = self.scrub()
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stderr, "")

    def test_history_check_covers_tags_branches_and_generic(self):
        self.write("a.md", "clean\n")
        self.assertEqual(self.git("add", "a.md").returncode, 0)
        self.assertEqual(self.git("commit", "-m", "chore: init").returncode, 0)

        self.assertEqual(self.git("tag", "-a", "v0.1.0", "-m", "for acmecorp").returncode, 0)
        self.assertEqual(self.scrub().returncode, 1)
        self.assertEqual(self.git("tag", "-d", "v0.1.0").returncode, 0)

        self.assertEqual(self.git("tag", "-a", "v0.1.1", "-m", "by a.b" "@example.org").returncode, 0)
        self.assertEqual(self.scrub().returncode, 1)
        self.assertEqual(self.scrub(CI="true").returncode, 1)
        self.assertEqual(self.git("tag", "-d", "v0.1.1").returncode, 0)

        self.assertEqual(self.git("checkout", "-b", "side").returncode, 0)
        self.assertEqual(self.git("commit", "--allow-empty", "-m", "note /Us" "ers/x").returncode, 0)
        self.assertEqual(self.git("checkout", "-").returncode, 0)
        self.assertEqual(self.scrub().returncode, 1)
        self.assertEqual(self.scrub(CI="true").returncode, 1)

    def test_manual_path_args_check_working_tree_like_commit_paths(self):
        self.write("a.md", "clean a\n")
        self.write("b.md", "clean b\n")
        self.assertEqual(self.git("add", "a.md", "b.md").returncode, 0)
        self.assertEqual(self.git("commit", "-m", "chore: init").returncode, 0)

        self.write("a.md", "mail a.b" "@example.org\n")
        self.assertEqual(self.scrub().returncode, 0)
        self.assertEqual(self.scrub("--", "a.md").returncode, 1)
        self.assertEqual(self.scrub("a.md").returncode, 1)

        self.write("a.md", "clean a\n")
        self.write("b.md", "acmecorp\n")
        self.assertEqual(self.git("add", "b.md").returncode, 0)
        self.assertEqual(self.scrub().returncode, 1)
        self.assertEqual(self.scrub("--", "a.md").returncode, 0)

        self.assertEqual(self.git("reset", "-q", "b.md").returncode, 0)
        self.write("b.md", "clean b\n")
        self.write("a.md", "acmecorp\n")
        self.assertEqual(self.git("add", "a.md").returncode, 0)
        self.write("a.md", "clean a\n")
        self.assertEqual(self.scrub().returncode, 1)
        self.assertEqual(self.scrub("--", "a.md").returncode, 0)

    def test_help_prints_usage_and_exits_0(self):
        (self.tmp / ".scrub-names").unlink()
        res = self.scrub("--help")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Usage:", res.stdout)


if __name__ == "__main__":
    unittest.main()
