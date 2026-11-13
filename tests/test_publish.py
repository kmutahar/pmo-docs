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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_fixture as tf  # noqa: E402
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
import docs_audit as da  # noqa: E402
import pmo_common as pc  # noqa: E402
import publish  # noqa: E402

TOOL = SCRIPTS / "publish.py"


def finished_text(h: str) -> str:
    raw = (REPO / "examples/acme/pmo/documents/Decision log.md").read_text(encoding="utf-8")
    return raw.replace(
        "status: draft",
        f"status: finished\nsource_hashes:\n  decisions: \"{h}\"",
        1,
    )


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
        f.write_text(finished_text(h), encoding="utf-8")
        return f

    def finish_translation(self, orig_file, lang="xx", dir_="rtl"):
        orig_text = orig_file.read_text(encoding="utf-8")
        trans_text = tf.make_translation(orig_text, lang=lang, dir_=dir_)
        fm, body = pc.split_front_matter(trans_text)
        fm["status"] = "finished"
        fm["last_updated"] = "2026-03-15"
        import yaml
        new_text = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n{body}"
        f = self.docs / f"Decision log.{lang}.md"
        f.write_text(new_text, encoding="utf-8")
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

    def test_translation_is_published_like_any_finished_document(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        tf.enable_languages(self.root, ("xx",))
        src = self.finish_decision_log()
        trans = self.finish_translation(src)

        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("new: Decision log.xx.md", out)

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.xx.md", out)

        pub_file = self.root / "published/Decision log.xx.md"
        self.assertTrue(pub_file.exists())
        self.assertEqual(pub_file.read_bytes(), trans.read_bytes())

    def test_translation_behind_is_stale(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        tf.enable_languages(self.root, ("xx",))
        src = self.finish_decision_log()
        self.finish_translation(src)

        # Modify original body so translation is behind
        src.write_text(src.read_text(encoding="utf-8") + "\nModified body.\n", encoding="utf-8")

        # Dry run lists it as stale
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("stale: Decision log.xx.md", out)

        # Apply without --include skips it and exits 1
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 1)
        self.assertFalse((self.root / "published/Decision log.xx.md").exists())

        # Apply with --include copies it
        code, out, _ = run(self.root, "--apply", "--include", "Decision log.xx.md")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.xx.md", out)
        self.assertTrue((self.root / "published/Decision log.xx.md").exists())


    def write_finished(self, rel, text=None, ty="decision-log"):
        """A finished decision log whose source hash is current (so it is not stale), at rel under the documents folder."""
        f = self.docs / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        h = da.register_hash(self.root, pc.load_config(self.root), "decisions")
        f.write_text(text if text is not None else finished_text(h), encoding="utf-8")
        return f

    def test_invalid_mode_exits_2(self):
        self.base_config = (self.root / "pmo/config.yaml").read_text(encoding="utf-8")
        for mode in ("ftp", "Folder", "''", "[folder]"):
            with self.subTest(mode=mode):
                (self.root / "pmo/config.yaml").write_text(self.base_config, encoding="utf-8")
                self.set_config(f"publish:\n  mode: {mode}\n  path: published\n")
                code, _, err = run(self.root)
                self.assertEqual(code, 2)
                self.assertIn("invalid publish mode", err)

    def test_missing_blank_or_non_string_path_exits_2(self):
        for line in ("", "  path: null\n", "  path: ''\n", "  path: '   '\n", "  path: 5\n", "  path: [a]\n"):
            for mode in ("folder", "repo"):
                with self.subTest(path=line, mode=mode):
                    (self.root / "pmo/config.yaml").write_text(f"publish:\n  mode: {mode}\n{line}", encoding="utf-8")
                    code, _, err = run(self.root)
                    self.assertEqual(code, 2)
                    self.assertIn("publish.path must be a non-empty string", err)

    def test_publish_null_or_missing_block_means_mode_none(self):
        (self.root / "pmo/config.yaml").write_text("publish: null\n", encoding="utf-8")
        code, out, _ = run(self.root, "--apply")
        self.assertEqual((code, "mode is none" in out), (0, True))

    def test_folder_path_that_contains_the_documents_folder_exits_2(self):
        for path in ("pmo", ".", "./pmo/documents"):
            with self.subTest(path=path):
                (self.root / "pmo/config.yaml").write_text(f"publish:\n  mode: folder\n  path: '{path}'\n", encoding="utf-8")
                code, _, err = run(self.root)
                self.assertEqual(code, 2)
                self.assertIn("ERROR", err)

    def test_folder_path_absolute_or_into_dot_git_exits_2(self):
        for path in (str(self.tmp / "elsewhere"), ".git/pub", "x/../../out"):
            with self.subTest(path=path):
                (self.root / "pmo/config.yaml").write_text(f"publish:\n  mode: folder\n  path: '{path}'\n", encoding="utf-8")
                code, _, err = run(self.root)
                self.assertEqual(code, 2)
                self.assertIn("must be inside the project", err)

    def test_repo_mode_folder_that_does_not_exist_exits_2(self):
        self.set_config(f"publish:\n  mode: repo\n  path: '{self.tmp / 'nope'}'\n")
        code, _, err = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("repo folder not found", err)

    def test_repo_mode_relative_path_is_taken_from_the_project(self):
        repo = self.root / "sibling"
        repo.mkdir()
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        self.set_config("publish:\n  mode: repo\n  path: sibling\n")
        self.finish_decision_log()
        code, out, err = run(self.root, "--apply")
        self.assertEqual(code, 0, err)
        self.assertTrue((repo / "Decision log.md").is_file())

    def test_dry_run_prints_url_only_for_new_documents_and_trims_the_slash(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n  url: https://example.test/docs//\n")
        self.finish_decision_log()
        self.write_finished("Sub dir/Notes.md")
        out = run(self.root)[1]
        self.assertIn("new: Decision log.md\nurl: https://example.test/docs/Decision%20log.md", out)
        self.assertIn("url: https://example.test/docs/Sub%20dir/Notes.md", out)
        run(self.root, "--apply")
        out = run(self.root)[1]
        self.assertIn("unchanged: Decision log.md", out)
        self.assertNotIn("url:", out)

    def test_nested_documents_keep_their_folders_and_unicode_names_and_bytes(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        a = self.write_finished("مشاريع/تقرير شهري.md")
        a.write_bytes(a.read_bytes() + "\r\nتقرير\r\nline\xa0two\n".encode("utf-8"))
        code, out, err = run(self.root, "--apply")
        self.assertEqual(code, 0, err)
        self.assertIn("copied: مشاريع/تقرير شهري.md", out)
        self.assertEqual((self.root / "published/مشاريع/تقرير شهري.md").read_bytes(), a.read_bytes())

    def test_finished_document_of_unknown_or_missing_type_is_not_listed_or_counted(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.write_finished("Unknown.md", "---\ntype: no-such-type\nstatus: finished\n---\n# x\n")
        self.write_finished("Untyped.md", "---\nstatus: finished\n---\n# x\n")
        self.write_finished("Plain.md", "# no front matter\n")
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown.md", out)
        self.assertNotIn("Untyped.md", out)
        self.assertIn("drafts: 3", out)  # the plain file, the Acme status report and the Acme decision log
        self.assertIn("excluded: 0", out)

    def test_status_other_than_finished_is_a_draft(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        for n, st in enumerate(("Finished", "done", "", "null", "[finished]")):
            self.write_finished(f"D{n}.md", f"---\ntype: decision-log\nstatus: {st or chr(39)*2}\n---\n# x\n")
        out = run(self.root)[1]
        self.assertNotIn("new:", out)
        self.assertIn("drafts: 7", out)  # five here plus the two Acme drafts

    def test_a_file_that_is_not_utf8_is_skipped_as_a_draft(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        (self.docs / "Binary.md").write_bytes(b"---\ntype: decision-log\nstatus: finished\n---\n\xff\xfe\n")
        code, out, err = run(self.root)
        self.assertEqual(code, 0, err)
        self.assertNotIn("Binary.md", out)
        self.assertNotIn("Traceback", err)

    def test_front_matter_that_is_invalid_yaml_counts_as_a_draft(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.write_finished("Broken.md", "---\ntype: [\nstatus: finished\n---\n# x\n")
        code, out, err = run(self.root)
        self.assertEqual(code, 0, err)
        self.assertNotIn("Broken.md", out)

    def test_missing_documents_folder_lists_nothing(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        shutil.rmtree(self.docs)
        code, out, _ = run(self.root, "--apply")
        self.assertEqual((code, out), (0, ""))

    def test_apply_with_nothing_to_publish_exits_0(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertNotIn("copied", out)

    def test_overwrite_of_a_new_document_just_copies_it(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        code, out, _ = run(self.root, "--apply", "--overwrite", "Decision log.md", "--overwrite", "Decision log.md")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("copied: Decision log.md"), 1)

    def test_stale_document_rules_when_the_target_exists_and_differs(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        dec = self.root / "pmo/registers/decisions.yaml"
        dec.write_text(dec.read_text(encoding="utf-8") + "\n# change\n", encoding="utf-8")
        target = self.root / "published/Decision log.md"
        target.parent.mkdir()
        target.write_text("Old target.\n", encoding="utf-8")
        self.assertIn("stale, conflict: Decision log.md", run(self.root)[1])
        # include alone does not overwrite a differing target
        code, out, _ = run(self.root, "--apply", "--include", "Decision log.md")
        self.assertEqual((code, target.read_text(encoding="utf-8")), (1, "Old target.\n"))
        # overwrite alone does not publish a stale document
        code, out, _ = run(self.root, "--apply", "--overwrite", "Decision log.md")
        self.assertEqual((code, target.read_text(encoding="utf-8")), (1, "Old target.\n"))
        # both do
        code, out, _ = run(self.root, "--apply", "--include", "Decision log.md", "--overwrite", "Decision log.md")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)
        self.assertNotEqual(target.read_text(encoding="utf-8"), "Old target.\n")

    def test_apply_copies_what_it_can_and_exits_1_for_what_it_left(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        self.write_finished("Other.md")
        (self.root / "published").mkdir()
        (self.root / "published/Other.md").write_text("different\n", encoding="utf-8")
        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 1)
        self.assertIn("copied: Decision log.md", out)
        self.assertNotIn("\ncopied: Other.md", "\n" + out)  # "uncopied:" contains "copied:"
        self.assertIn("uncopied: Other.md", out)
        self.assertEqual((self.root / "published/Other.md").read_text(encoding="utf-8"), "different\n")

    def test_old_document_is_not_stale_but_a_moved_as_of_does_not_change_the_state(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        out = run(self.root, "--as-of", "2030-01-01")[1]
        self.assertIn("new: Decision log.md", out)  # `old` is an audit finding, not a stale check

    def test_as_of_must_be_a_real_date(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        for bad in ("2026-02-30", "soon", ""):
            code, _, err = run(self.root, "--as-of", bad)
            self.assertEqual(code, 2, bad)

    def test_target_folder_that_is_a_file_exits_2_without_a_traceback(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        (self.root / "published").write_text("i am a file\n", encoding="utf-8")
        code, _, err = run(self.root, "--apply")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_sub_folder_that_links_out_of_the_target_exits_2_and_copies_nothing(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.write_finished("sub/Notes.md")
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.root / "published").mkdir()
        os.symlink(outside, self.root / "published/sub")
        code, _, err = run(self.root, "--apply")
        self.assertEqual(code, 2)
        self.assertIn("escapes publish directory", err)
        self.assertEqual(list(outside.iterdir()), [])

    def test_invalid_finished_document_is_listed_and_not_copied(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        f = self.finish_decision_log()
        f.write_text(f.read_text(encoding="utf-8") + "\n{{placeholder}}\n", encoding="utf-8")

        code, out, _ = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("invalid: Decision log.md\n  unreplaced {{placeholder}} left in text", out)

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 1)
        self.assertIn("uncopied: Decision log.md (invalid: fix the errors listed by structure_check.py)", out)
        self.assertFalse((self.root / "published/Decision log.md").exists())

    def test_valid_finished_document_still_publishes(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()

        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("new: Decision log.md", out)

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)
        self.assertTrue((self.root / "published/Decision log.md").exists())

    def test_stale_and_conflict_show_both_words(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        dec = self.root / "pmo/registers/decisions.yaml"
        dec.write_text(dec.read_text(encoding="utf-8") + "\n# change\n", encoding="utf-8")
        target = self.root / "published/Decision log.md"
        target.parent.mkdir()
        target.write_text("Old target.\n", encoding="utf-8")

        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("stale, conflict: Decision log.md", out)

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 1)
        self.assertIn("uncopied: Decision log.md (stale, conflict: pass --include Decision log.md and --overwrite Decision log.md)", out)
        self.assertEqual(target.read_text(encoding="utf-8"), "Old target.\n")

        code, out, _ = run(self.root, "--apply", "--include", "Decision log.md")
        self.assertEqual(code, 1)
        self.assertIn("uncopied: Decision log.md (conflict: pass --overwrite Decision log.md)", out)
        self.assertEqual(target.read_text(encoding="utf-8"), "Old target.\n")

        code, out, _ = run(self.root, "--apply", "--include", "Decision log.md", "--overwrite", "Decision log.md")
        self.assertEqual(code, 0)
        self.assertIn("copied: Decision log.md", out)
        self.assertNotEqual(target.read_text(encoding="utf-8"), "Old target.\n")

    def test_each_left_document_gets_an_uncopied_line(self):
        self.set_config("publish:\n  mode: folder\n  path: published\n")
        self.finish_decision_log()
        dec = self.root / "pmo/registers/decisions.yaml"
        dec.write_text(dec.read_text(encoding="utf-8") + "\n# change\n", encoding="utf-8")
        target = self.root / "published/Decision log.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Old target.\n", encoding="utf-8")

        self.write_finished("Other.md")

        code, out, _ = run(self.root, "--apply")
        self.assertEqual(code, 1)
        self.assertIn("copied: Other.md", out)
        self.assertIn("uncopied: Decision log.md (stale, conflict: pass --include Decision log.md and --overwrite Decision log.md)", out)

    def test_help_and_usage_errors(self):
        self.assertEqual(subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True).returncode, 0)
        self.assertEqual(run(self.root, "--bogus")[0], 2)
        self.assertEqual(run(self.root, "--overwrite")[0], 2)  # needs a value
        self.assertEqual(subprocess.run([sys.executable, str(TOOL), "--project", str(self.tmp / "nope")], capture_output=True).returncode, 2)

if __name__ == "__main__":
    unittest.main()
