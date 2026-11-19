# Tests dev/release (--help, version and tag checks, dirty tree, dry run, the non-dry path up to the first prompt and, through a pseudo-terminal, the commit, tag and push steps and their failures, with stub git-cliff/claude) in a throwaway git repo.
# Run from the repo root: python3 -m unittest tests.test_release
import json
import os
import pty
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
        for rel in ("dev/release", "skills/pmo-docs/SKILL.md", "skills/pmo-docs/.claude-plugin/plugin.json", "README.md", "docs/INSTALL_FOR_AGENTS.md"):
            (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.tmp / rel)
        self.git("init", "-q", "-b", "dev")
        self.git("add", ".")
        self.git("commit", "-qm", "init")

    def git(self, *args, check=True, cwd=None):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.t",
               "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        r = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                           cwd=cwd or self.tmp, env=env, capture_output=True, text=True)
        if check:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def release(self, *args, **env):
        # no terminal and no stdin: a prompt could only read EOF, which counts as No
        env = {**{k: v for k, v in os.environ.items() if k not in ("DRY_RUN", "RELEASE_SKIP_CHECKS")},
               "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
               "RELEASE_SKIP_CHECKS": "1", "PYTHONDONTWRITEBYTECODE": "1", **env}
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
        with open(self.tmp / "skills/pmo-docs/.claude-plugin/plugin.json", "a", encoding="utf-8") as f:
            f.write("\n")
        self.assertEqual(self.release("--dry-run", "--allow-dirty", "9.9.9").returncode, 1)

    def test_dirty_changelog_refused_even_with_allow_dirty(self):
        (self.tmp / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        self.git("add", "CHANGELOG.md")
        self.git("commit", "-qm", "changelog")
        (self.tmp / "CHANGELOG.md").write_text("# Changelog\nedited\n", encoding="utf-8")
        r = self.release("--dry-run", "--allow-dirty", "9.9.9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("CHANGELOG.md", r.stderr)
        self.assertIn("release files", r.stderr)

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
            "#!/bin/sh\n[ \"$1\" = \"-o\" ] && exec > \"$2\"\ncat <<'EOF'\n# Changelog\n\n## [9.9.9] - 2026-01-01\n\n- stub\nEOF\n",
            encoding="utf-8",
        )
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
        self.assertEqual(json.loads((self.tmp / "skills/pmo-docs/.claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"], "9.9.9")
        self.assertEqual((self.tmp / "CHANGELOG.md").read_text(encoding="utf-8"), "# Changelog\n\n## [9.9.9] - 2026-01-01\n\n- stub\n")
        self.assertIn("- stub", r.stdout)
        names = self.git("diff", "--name-only").stdout.split()
        self.assertEqual(sorted(names), ["README.md", "docs/INSTALL_FOR_AGENTS.md", "skills/pmo-docs/.claude-plugin/plugin.json", "skills/pmo-docs/SKILL.md"])
        for rel in ("README.md", "docs/INSTALL_FOR_AGENTS.md"):
            text = (self.tmp / rel).read_text(encoding="utf-8")
            self.assertIn("v9.9.9", text, rel)
            self.assertNotIn("v0.5.0", text, rel)

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
        self.assertIn("validation failed", r.stderr)
        self.assertFalse((self.tmp / "CHANGELOG.md").exists())

    def test_missing_changelog_section_stops_before_commit_and_tag(self):
        env = self.stub_non_dry()
        before = self.git("rev-parse", "HEAD").stdout
        (Path(env["PATH"].split(os.pathsep)[0]) / "git-cliff").write_text(
            "#!/bin/sh\n[ \"$1\" = \"-o\" ] && exec > \"$2\"\ncat <<'EOF'\n# Changelog\n\n## [0.7.4] - 2026-01-01\n\n- old\nEOF\n",
            encoding="utf-8",
        )
        dry = self.release("--dry-run", "9.9.9", RELEASE_SKIP_CHECKS="0", **env)
        self.assertEqual(dry.returncode, 1)
        self.assertIn("no section for 9.9.9", dry.stderr)
        r = self.release("9.9.9", **env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no section for 9.9.9", r.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, before)
        self.assertEqual(self.git("tag").stdout, "")

    def test_release_notes_preview_cut_from_written_changelog(self):
        env = self.stub_non_dry()
        (Path(env["PATH"].split(os.pathsep)[0]) / "git-cliff").write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"-o\" ]; then\n"
            "  cat <<'EOF' > \"$2\"\n# Changelog\n\n## [9.9.9] - 2026-01-01\n\n- new change\n\n## [9.9.8] - 2025-12-01\n\n- old change\nEOF\n"
            "else\n"
            "  echo \"wrong-unreleased\"\n"
            "fi\n",
            encoding="utf-8",
        )
        r = self.release("9.9.9", **env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Aborted.", r.stderr)
        self.assertIn("- new change", r.stdout)
        self.assertNotIn("- old change", r.stdout)
        self.assertNotIn("wrong-unreleased", r.stdout)

    def test_tag_on_origin_rejected_before_commit(self):
        remote = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, remote)
        self.git("init", "--bare", "-q", str(remote), cwd=remote)
        self.git("remote", "add", "origin", str(remote))
        self.git("push", "-q", "origin", "dev")
        self.git("tag", "v9.9.9")
        self.git("push", "-q", "origin", "v9.9.9")
        self.git("tag", "-d", "v9.9.9")
        before = self.git("rev-parse", "HEAD").stdout
        r = self.release("--dry-run", "9.9.9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("exists on origin", r.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, before)
        ok = self.release("--dry-run", "9.9.8")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertNotIn("warning:", ok.stderr.lower())

    def test_non_dev_branch_rejected(self):
        self.git("checkout", "-qb", "feature")
        r = self.release("--dry-run", "9.9.9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("from dev", r.stderr)

    def test_unreachable_origin_warns_and_continues(self):
        self.git("remote", "add", "origin", str(self.tmp / "missing-remote.git"))
        r = self.release("--dry-run", "9.9.9")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning:", r.stderr.lower())


    def release_tty(self, version, answers, **env):
        """Run dev/release on a pseudo-terminal (its prompts read /dev/tty) and answer each [y/N] prompt in order. Returns (exit code, output)."""
        env = {**{k: v for k, v in os.environ.items() if k not in ("DRY_RUN", "RELEASE_SKIP_CHECKS")},
               "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.t",
               "RELEASE_SKIP_CHECKS": "1", "PYTHONDONTWRITEBYTECODE": "1", **env}
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.tmp)
            os.execvpe("bash", ["bash", "dev/release", version], env)
        out, seen, answers = b"", 0, list(answers)
        while True:
            try:
                data = os.read(fd, 4096)
            except OSError:  # the child closed the terminal
                break
            if not data:
                break
            out += data
            while out.count(b"[y/N]") > seen and answers:
                os.write(fd, answers.pop(0).encode() + b"\n")
                seen += 1
        os.close(fd)
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status), out.decode("utf-8", "replace")

    def bare_origin(self):
        remote = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, remote)
        self.git("init", "--bare", "-q", str(remote), cwd=remote)
        self.git("remote", "add", "origin", str(remote))
        self.git("push", "-q", "-u", "origin", "dev")
        return remote

    def hook(self, repo_git_dir, name, body):
        path = Path(repo_git_dir) / "hooks" / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def test_yes_to_both_prompts_commits_tags_and_pushes(self):
        env = self.stub_non_dry()
        remote = self.bare_origin()
        code, out = self.release_tty("9.9.9", ["y", "y"], **env)
        self.assertEqual(code, 0, out)
        self.assertIn("Committed and tagged v9.9.9.", out)
        self.assertEqual(self.git("log", "-1", "--format=%s").stdout.strip(), "chore(release): v9.9.9")
        self.assertEqual(self.git("rev-parse", "v9.9.9^{commit}").stdout, self.git("rev-parse", "HEAD").stdout)
        self.assertEqual(self.git("rev-parse", "dev", cwd=remote).stdout, self.git("rev-parse", "HEAD").stdout)
        # the release workflow moves main after the checks pass; the script never does
        self.assertNotEqual(self.git("rev-parse", "--verify", "-q", "main", cwd=remote, check=False).returncode, 0)
        self.assertIn("v9.9.9", self.git("tag", cwd=remote).stdout)

    def test_no_to_push_leaves_commit_and_tag_local(self):
        env = self.stub_non_dry()
        remote = self.bare_origin()
        code, out = self.release_tty("9.9.9", ["y", "n"], **env)
        self.assertEqual(code, 0, out)
        self.assertIn("Not pushed.", out)
        self.assertIn("v9.9.9", self.git("tag").stdout)
        self.assertEqual(self.git("tag", cwd=remote).stdout, "")

    def test_commit_failure_leaves_head_and_prints_the_undo(self):
        env = self.stub_non_dry()
        self.hook(self.tmp / ".git", "pre-commit", "echo rejected >&2\nexit 1\n")
        before = self.git("rev-parse", "HEAD").stdout
        code, out = self.release_tty("9.9.9", ["y"], **env)
        self.assertNotEqual(code, 0, out)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, before)
        self.assertEqual(self.git("tag").stdout, "")
        self.assertIn("To undo:", out)

    def test_tag_failure_keeps_the_commit_and_says_how_to_tag(self):
        env = self.stub_non_dry()
        # a post-commit hook that takes the tag name makes `git tag -a` fail after the commit exists
        self.hook(self.tmp / ".git", "post-commit", "git tag v9.9.9 HEAD\n")
        code, out = self.release_tty("9.9.9", ["y"], **env)
        self.assertNotEqual(code, 0, out)
        self.assertIn("the release commit exists but tagging failed", out)
        self.assertEqual(self.git("log", "-1", "--format=%s").stdout.strip(), "chore(release): v9.9.9")

    def test_push_failure_keeps_commit_and_tag_local_and_says_how_to_retry(self):
        env = self.stub_non_dry()
        remote = self.bare_origin()
        self.hook(remote, "pre-receive", "echo refused >&2\nexit 1\n")
        code, out = self.release_tty("9.9.9", ["y", "y"], **env)
        self.assertNotEqual(code, 0, out)
        self.assertIn("push failed; commit and tag are local only", out)
        self.assertIn("git push --atomic origin HEAD v9.9.9", out)
        self.assertIn("v9.9.9", self.git("tag").stdout)
        self.assertEqual(self.git("tag", cwd=remote).stdout, "")

    def test_behind_upstream_warns_and_continues(self):
        remote = self.bare_origin()
        other = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, other)
        self.git("clone", "-q", "-b", "dev", str(remote), str(other / "c"), cwd=other)
        (other / "c" / "new.txt").write_text("x", encoding="utf-8")
        self.git("add", ".", cwd=other / "c")
        self.git("commit", "-qm", "ahead", cwd=other / "c")
        self.git("push", "-q", "origin", "dev", cwd=other / "c")
        self.git("fetch", "-q", "origin")
        r = self.release("--dry-run", "9.9.9")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("behind its upstream", r.stderr)


if __name__ == "__main__":
    unittest.main()
