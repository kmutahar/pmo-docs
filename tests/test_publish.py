"""Tests for scripts/publish.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest discover tests"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
import docs_audit as da  # noqa: E402
import pmo_common as pc  # noqa: E402
import publish  # noqa: E402

TOOL = SCRIPTS / "publish.py"


def run(project, *args):
    p = subprocess.run([sys.executable, str(TOOL), "--project", str(project), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class Publish(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.docs = self.root / "pmo/documents"
        # the user's git config (gpgsign, hook templates) must not reach the test repos
        env = mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"})
        env.start()
        self.addCleanup(env.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def set_config(self, extra_yaml: str):
        cfg_path = self.root / "pmo/config.yaml"
        cfg_text = cfg_path.read_text(encoding="utf-8")
        cfg_path.write_text(cfg_text + "\n" + extra_yaml + "\n", encoding="utf-8")

    def finish_decision_log(self):
        cfg = pc.load_config(self.root)
        h = da.register_hash(self.root, cfg, "decisions")
        f = self.docs / "Decision log.md"
        f.write_text(
            f"---\ntitle: \"Decision log - Acme Portal\"\ntype: decision-log\nproject: \"Acme Portal\"\n"
            f"manager: \"Sam Example\"\ntemplate_version: 1\nstatus: finished\nlast_updated: 2026-03-15\n"
            f"source_hashes:\n  decisions: \"{h}\"\n---\n# Decision log\n\nContent here.\n",
            encoding="utf-8"
        )
        return f

    def test_mode_none_exits_0_and_writes_nothing(self):
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("publish mode is none", out)

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertIn("publish mode is none", out)

    def test_listing_writes_nothing(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()

        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("new: Decision log.md", out)
        self.assertFalse((self.root / "published").exists())

    def test_apply_copies_new_files_byte_identical(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        src = self.finish_decision_log()

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)

        pub_file = self.root / "published/Decision log.md"
        self.assertTrue(pub_file.exists())
        self.assertEqual(pub_file.read_bytes(), src.read_bytes())

    def test_second_apply_is_unchanged(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()

        # First apply
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)

        # Second apply
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertNotIn("copied:", out)

        # Listing says unchanged
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("unchanged: Decision log.md", out)

    def test_conflict_left_alone_without_overwrite_exits_1(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()

        # Initial copy
        run(self.root, "--apply")

        # Create conflict in target
        pub_file = self.root / "published/Decision log.md"
        pub_file.write_text("Modified target.\n", encoding="utf-8")

        # Listing reports conflict
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("conflict: Decision log.md", out)

        # Apply without overwrite exits 1
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 1)
        self.assertEqual(pub_file.read_text(encoding="utf-8"), "Modified target.\n")

    def test_overwrite_copies_it(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        src = self.finish_decision_log()
        run(self.root, "--apply")

        pub_file = self.root / "published/Decision log.md"
        pub_file.write_text("Modified target.\n", encoding="utf-8")

        code, out, _ = run(self.root, "--apply", "--overwrite", "Decision log.md")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)
        self.assertEqual(pub_file.read_bytes(), src.read_bytes())

    def test_drafts_and_excluded_types_are_not_listed(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        # Ensure status report is draft
        (self.docs / "2026-03 - Status report.md").write_text(
            "---\ntype: status-report\nstatus: draft\n---\n# Draft report\n", encoding="utf-8"
        )
        # Add a finished docs-audit-report (which has publish: false in default config)
        (self.docs / "2026-03 - Documentation audit.md").write_text(
            "---\ntype: docs-audit-report\nstatus: finished\nlast_updated: 2026-03-15\n---\n# Audit\n", encoding="utf-8"
        )
        self.finish_decision_log()

        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("new: Decision log.md", out)
        self.assertNotIn("Status report.md", out)
        self.assertNotIn("Documentation audit.md", out)
        self.assertIn("drafts: 1", out)
        self.assertIn("excluded: 1", out)

    def test_stale_skipped_unless_included(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        src = self.finish_decision_log()

        # Modify decisions register so hash changes
        dec_file = self.root / "pmo/registers/decisions.yaml"
        dec_file.write_text(dec_file.read_text(encoding="utf-8") + "\n# change\n", encoding="utf-8")

        # Listing says stale
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("stale: Decision log.md", out)

        # Apply without --include exits 1 and copies nothing
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 1)
        self.assertFalse((self.root / "published/Decision log.md").exists())

        # Apply with --include copies it
        code, out, _ = run(self.root, "--apply", "--include", "Decision log.md")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)
        self.assertTrue((self.root / "published/Decision log.md").exists())

    def test_folder_path_outside_project_exits_2(self):
        self.set_config("publish:\n  mode: folder\n  path: ../outside\n")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_folder_path_inside_documents_exits_2(self):
        self.set_config("publish:\n  mode: folder\n  path: pmo/documents/published\n")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("paths.documents", err)

        cfg_path = self.root / "pmo/config.yaml"
        cfg_path.write_text("publish:\n  mode: folder\n  path: pmo/documents\n", encoding="utf-8")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("paths.documents", err)

    def test_symlink_out_exits_2(self):
        target = self.tmp / "ext_target"
        target.mkdir()
        link = self.root / "pmo/symlink_out"
        os.symlink(target, link)
        self.set_config("publish:\n  mode: folder\n  path: pmo/symlink_out\n")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_repo_mode_requires_repo_top_level(self):
        repo_dir = self.tmp / "ext_repo"
        repo_dir.mkdir()

        # Plain folder -> exit 2
        self.set_config(f"publish:\n  mode: repo\n  path: '{repo_dir}'\n")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("not a git repository", err)

        # Git init repo
        subprocess.run(["git", "init", str(repo_dir)], check=True, capture_output=True)

        # Subfolder of a repo -> exit 2
        sub = repo_dir / "sub"
        sub.mkdir()
        cfg_path = self.root / "pmo/config.yaml"
        cfg_text = cfg_path.read_text(encoding="utf-8")
        cfg_path.write_text(cfg_text.replace(str(repo_dir), str(sub)), encoding="utf-8")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("not the top level", err)

        # Project's own repo -> exit 2
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        cfg_path.write_text(cfg_text.replace(str(repo_dir), str(self.root)), encoding="utf-8")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("cannot be the project repository itself", err)

        # Real separate repo top level -> exit 0
        cfg_path.write_text(cfg_text, encoding="utf-8")
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)

    def test_repo_mode_never_commits(self):
        repo_dir = self.tmp / "target_repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init", str(repo_dir)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(repo_dir), "config", "user.email", "noreply"], check=True)
        (repo_dir / "init.txt").write_text("initial commit\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo_dir), "add", "init.txt"], check=True)
        subprocess.run(["git", "-C", str(repo_dir), "-c", "commit.gpgsign=false", "commit", "-m", "init"], check=True, capture_output=True)

        self.set_config(f"publish:\n  mode: repo\n  path: '{repo_dir}'\n")
        self.finish_decision_log()

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)

        # git status shows file is untracked
        st = subprocess.run(["git", "-C", str(repo_dir), "status", "--porcelain"],
                            capture_output=True, text=True, check=True)
        self.assertIn("Decision log.md", st.stdout)
        self.assertIn("??", st.stdout)

        # git log has only the initial commit
        lg = subprocess.run(["git", "-C", str(repo_dir), "log", "--oneline"],
                            capture_output=True, text=True, check=True)
        lines = lg.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("init", lines[0])

    def test_stale_but_already_published_is_unchanged(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        run(self.root, "--apply")
        dec_file = self.root / "pmo/registers/decisions.yaml"
        dec_file.write_text(dec_file.read_text(encoding="utf-8") + "\n# change\n", encoding="utf-8")

        code, out, _ = run(self.root)
        self.assertIn("unchanged: Decision log.md", out)
        self.assertNotIn("stale:", out)
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertNotIn("copied:", out)

    def test_unknown_flags_are_refused_on_a_dry_run_too(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        for flag in ("--overwrite", "--include"):
            code, _, err = run(self.root, flag, "nonexistent.md")
            self.assertEqual(code, 2, flag)
            self.assertIn("not a candidate", err)

    def test_publish_that_is_not_a_map_exits_2_without_traceback(self):
        self.set_config("publish: folder")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)
        self.assertNotIn("Traceback", err)

    def test_document_type_that_is_not_a_string_does_not_crash(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        (self.docs / "Odd.md").write_text("---\ntype: [x]\nstatus: finished\n---\n# Odd\n", encoding="utf-8")
        code, out, err = run(self.root)
        self.assertEqual(code, 0, err)
        self.assertNotIn("Odd.md", out)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file permissions")
    def test_copy_failure_exits_2_and_leaves_the_target_whole(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        pub = self.root / "published"
        pub.mkdir()
        target = pub / "Decision log.md"
        target.write_text("Old target.\n", encoding="utf-8")
        pub.chmod(0o500)
        try:
            code, _, err = run(self.root, "--apply", "--overwrite", "Decision log.md")
        finally:
            pub.chmod(0o700)  # tearDown runs before addCleanup, so restore here
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)
        self.assertIn("Decision log.md", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(target.read_text(encoding="utf-8"), "Old target.\n")
        self.assertEqual(sorted(p.name for p in pub.iterdir()), ["Decision log.md"])

    def test_unknown_overwrite_exits_2_and_copies_nothing(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()

        code, _, err = run(self.root, "--apply", "--overwrite", "nonexistent.md")
        self.assertEqual(code, 2)
        self.assertIn("not a candidate", err)
        self.assertFalse((self.root / "published").exists())


if __name__ == "__main__":
    unittest.main()
