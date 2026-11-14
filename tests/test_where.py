"""Tests for scripts/where.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_where"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_fixture as tf  # noqa: E402
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402
TOOL = REPO / "skills/pmo-docs/scripts/where.py"


def run(project, *args):
    p = subprocess.run([sys.executable, str(TOOL), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def fields(out):
    return dict(line.split(": ", 1) for line in out.splitlines() if ": " in line)


class Where(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_document_with_period(self):
        code, out, _ = run(self.root, "status-report", "2026-03")
        f = fields(out)
        self.assertEqual(code, 0)
        self.assertEqual(f["type"], "status-report")
        self.assertEqual(f["document"], "pmo/documents/2026-03 - Status report.md")
        self.assertEqual(f["document_exists"], "yes")
        self.assertIn("tasks", f["generated_from"].split(", "))
        self.assertEqual(f["stale_days"], "30")

    def test_period_must_look_like_a_period(self):
        for bad in ("../../x", "2026/03", "March", "2026-3", "2026", "2026-Q1"):
            code, out, err = run(self.root, "status-report", bad)
            self.assertEqual(code, 2, bad)
            self.assertIn("invalid period", err)
        for good in ("2026-03", "2026-W10"):
            self.assertEqual(run(self.root, "status-report", good)[0], 0, good)

    def test_document_without_period_in_name(self):
        f = fields(run(self.root, "decision-log")[1])
        self.assertEqual(f["document"], "pmo/documents/Decision log.md")
        self.assertEqual(f["document_exists"], "yes")

    def test_missing_document(self):
        f = fields(run(self.root, "status-report", "2030-01")[1])
        self.assertEqual(f["document_exists"], "no")

    def test_period_defaults_to_current_month(self):
        f = fields(run(self.root, "status-report", "--as-of", "2026-03-15")[1])
        self.assertEqual(f["document"], "pmo/documents/2026-03 - Status report.md")

    def test_week_option(self):
        f = fields(run(self.root, "status-report", "--week", "--as-of", "2026-03-15")[1])
        self.assertEqual(f["document"], "pmo/documents/2026-W11 - Status report.md")

    def test_week_start_saturday_and_window(self):
        # Monday default
        f = fields(run(self.root, "status-report", "--week", "--as-of", "2026-11-07")[1])
        self.assertEqual(f["document"], "pmo/documents/2026-W45 - Status report.md")
        self.assertEqual(f["window"], "2026-11-02..2026-11-08")

        # Saturday start written into temp Acme config
        cfg_path = self.root / "pmo/config.yaml"
        cfg_text = cfg_path.read_text(encoding="utf-8")
        # add the key inside the existing project map; a second project: key would replace it
        cfg_path.write_text(cfg_text.replace("project:\n", "project:\n  week_start: saturday\n", 1), encoding="utf-8")
        code, out, _ = run(self.root, "status-report", "--week", "--as-of", "2026-11-07")
        self.assertEqual(code, 0)
        f = fields(out)
        self.assertEqual(f["document"], "pmo/documents/2026-W46 - Status report.md")
        self.assertEqual(f["window"], "2026-11-07..2026-11-13")

    def test_month_period_window(self):
        f = fields(run(self.root, "status-report", "2026-03")[1])
        self.assertEqual(f["window"], "2026-03-01..2026-03-31")

    def test_week_that_does_not_exist_exits_2(self):
        code, _, err = run(self.root, "status-report", "2025-W53")
        self.assertEqual(code, 2)
        self.assertIn("Invalid week", err)

    def test_type_without_period_has_window_none(self):
        f = fields(run(self.root, "decision-log")[1])
        self.assertEqual(f["window"], "none")

    def test_bad_week_start_exits_2(self):
        cfg_path = self.root / "pmo/config.yaml"
        cfg_path.write_text("schema_version: 1\nproject:\n  week_start: someday\n", encoding="utf-8")
        code, _, err = run(self.root, "status-report")
        self.assertEqual(code, 2)
        self.assertIn("project.week_start must be one of monday..sunday", err)

    def test_skill_template_when_no_override(self):
        f = fields(run(self.root, "status-report", "2026-03")[1])
        self.assertEqual(f["template_source"], "skill")
        self.assertTrue(f["template"].endswith("assets/templates/status-report.md"))

    def test_symlinked_template_leaving_the_project_is_an_error(self):
        tpl = self.root / "pmo/templates/status-report.md"
        tpl.parent.mkdir(parents=True, exist_ok=True)
        outside = self.root.parent / "outside.md"
        outside.write_text("x", encoding="utf-8")
        tpl.symlink_to(outside)
        code, out, err = run(self.root, "status-report", "2026-03")
        self.assertEqual(code, 2)
        self.assertIn("asset leaves project", err)
        self.assertNotIn("Traceback", err)

    def test_project_template_wins(self):
        tpl = self.root / "pmo/templates/status-report.md"
        tpl.parent.mkdir(parents=True)
        tpl.write_text("---\ntype: status-report\ntemplate_version: 3\nbased_on: status-report@2\n---\n# x\n", encoding="utf-8")
        f = fields(run(self.root, "status-report", "2026-03")[1])
        self.assertEqual(f["template_source"], "project")
        self.assertEqual(f["template"], "pmo/templates/status-report.md")
        self.assertEqual(f["template_exists"], "yes")
        self.assertEqual(f["template_version"], "3")
        self.assertEqual(f["based_on"], "status-report@2")
        self.assertEqual(f["drift"], "yes")

    def test_drift_state(self):
        # 1. drift: n/a when template is skill's own
        code, out, _ = run(self.root, "decision-log")
        self.assertEqual(code, 0)
        self.assertEqual(fields(out)["drift"], "n/a")

        # 2. drift: no for up-to-date override
        tpl = self.root / "pmo/templates/decision-log.md"
        tpl.parent.mkdir(parents=True, exist_ok=True)
        tpl.write_text("---\ntype: decision-log\ntemplate_version: 1\nbased_on: decision-log@1\n---\n# x\n", encoding="utf-8")
        code, out, _ = run(self.root, "decision-log")
        self.assertEqual(code, 0)
        self.assertEqual(fields(out)["drift"], "no")

        # 3. drift: yes for outdated override
        tpl.write_text("---\ntype: decision-log\ntemplate_version: 1\nbased_on: decision-log@0\n---\n# x\n", encoding="utf-8")
        code, out, _ = run(self.root, "decision-log")
        self.assertEqual(code, 0)
        self.assertEqual(fields(out)["drift"], "yes")

        # 4. drift: n/a for project template with no default
        cfg_file = self.root / "pmo/config.yaml"
        cfg_text = cfg_file.read_text(encoding="utf-8")
        cfg_file.write_text(cfg_text + "\ndoc_types:\n  custom:\n    title: Custom\n    template: custom.md\n    name: '{title}.md'\n", encoding="utf-8")
        cust_tpl = self.root / "pmo/templates/custom.md"
        cust_tpl.write_text("---\ntype: custom\n---\n# Custom\n", encoding="utf-8")
        code, out, _ = run(self.root, "custom")
        self.assertEqual(code, 0)
        self.assertEqual(fields(out)["drift"], "n/a")

    def test_unknown_type_exits_2_and_lists_types(self):
        code, _, err = run(self.root, "no-such-type")
        self.assertEqual(code, 2)
        self.assertIn("status-report", err)

    def test_hashes_skips_unknown_register(self):
        cfg = self.root / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8") + "\ndoc_types:\n  overdue-report:\n    generated_from: [tasks, nope]\n", encoding="utf-8")
        code, out, err = run(self.root, "overdue-report", "--hashes")
        self.assertEqual(code, 0, err)
        self.assertIn("tasks:", out)
        self.assertNotIn("nope", out.split("source_hashes", 1)[1])

    def test_hashes_option(self):
        import hashlib
        code, out, _ = run(self.root, "overdue-report", "--hashes")
        self.assertEqual(code, 0)
        h = hashlib.sha256((self.root / "pmo/registers/tasks.yaml").read_bytes()).hexdigest()[:8]
        self.assertIn(f'source_hashes: {{tasks: "{h}", ', out)
        (self.root / "pmo/registers/issues.yaml").unlink()
        self.assertIn('issues: "none"', run(self.root, "overdue-report", "--hashes")[1])
        self.assertNotIn("source_hashes", run(self.root, "docs-audit-report", "--hashes")[1])
        self.assertNotIn("source_hashes", run(self.root, "overdue-report")[1])

    def test_title_override_with_unicode_empty_and_slash(self):
        f = fields(run(self.root, "status-report", "2026-03", "--title", "تقرير ✓")[1])
        self.assertEqual(f["document"], "pmo/documents/2026-03 - تقرير ✓.md")
        self.assertEqual(f["title"], "تقرير ✓")
        code, _, err = run(self.root, "status-report", "2026-03", "--title", "a/b")
        self.assertEqual(code, 2)
        self.assertIn("title cannot contain '/'", err)
        for empty in ("", "   "):  # an empty title would give a name like "2026-03 - .md"
            code, _, err = run(self.root, "status-report", "2026-03", "--title", empty)
            self.assertEqual(code, 2, repr(empty))
            self.assertIn("title cannot be empty", err)

    def test_as_of_must_be_a_real_date(self):
        for bad in ("2026-02-30", "2026-13-01", "yesterday", "2026-3-1"):
            code, _, err = run(self.root, "status-report", "--as-of", bad)
            self.assertEqual(code, 2, bad)
            self.assertIn("--as-of", err)

    def test_as_of_boundaries_pick_the_period(self):
        for args, doc, window in (
            (("--as-of", "2024-02-29"), "2024-02", "2024-02-01..2024-02-29"),  # leap day, month
            (("--as-of", "2026-12-31", "--week"), "2026-W53", "2026-12-28..2027-01-03"),
            (("--as-of", "2027-01-03", "--week"), "2026-W53", "2026-12-28..2027-01-03"),
            (("--as-of", "2027-01-04", "--week"), "2027-W01", "2027-01-04..2027-01-10"),
            (("--as-of", "2026-12-31"), "2026-12", "2026-12-01..2026-12-31"),
            (("--as-of", "2026-01-01"), "2026-01", "2026-01-01..2026-01-31"),
        ):
            with self.subTest(args=args):
                f = fields(run(self.root, "status-report", *args)[1])
                self.assertEqual(f["document"], f"pmo/documents/{doc} - Status report.md")
                self.assertEqual(f["window"], window)

    def test_explicit_period_wins_over_week_and_as_of(self):
        f = fields(run(self.root, "status-report", "2026-04", "--week", "--as-of", "2026-12-31")[1])
        self.assertEqual((f["document"], f["window"]), ("pmo/documents/2026-04 - Status report.md", "2026-04-01..2026-04-30"))
        f = fields(run(self.root, "status-report", "2026-W10")[1])
        self.assertEqual(f["window"], "2026-03-02..2026-03-08")

    def test_bad_period_is_refused_even_for_a_type_without_period_in_its_name(self):
        for bad in ("2026-13", "2026-W54", "2026-1", "٢٠٢٦-٠٣"):
            code, _, err = run(self.root, "project-plan", bad)
            self.assertEqual(code, 2, bad)
            self.assertIn("invalid period", err)

    def test_week_start_changes_the_week_window_and_period(self):
        cfg_path = self.root / "pmo/config.yaml"
        cfg_text = cfg_path.read_text(encoding="utf-8")
        cfg_path.write_text(cfg_text.replace("project:\n", "project:\n  week_start: sunday\n", 1), encoding="utf-8")
        f = fields(run(self.root, "status-report", "--week", "--as-of", "2026-12-27")[1])
        self.assertEqual((f["document"], f["window"]), ("pmo/documents/2026-W53 - Status report.md", "2026-12-27..2027-01-02"))

    def test_lang_with_a_document_name_that_does_not_end_in_md_exits_2(self):
        tf.enable_languages(self.root, ("xx",))
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\ndoc_types:\n  decision-log:\n    name: '{title}.txt'\n", encoding="utf-8")
        code, out, err = run(self.root, "decision-log", "--lang", "xx")
        self.assertEqual(code, 2)
        self.assertIn("must end in '.md'", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(run(self.root, "decision-log")[0], 0)  # without --lang the name is fine

    def test_lang_with_missing_original_and_hashes_prints_none(self):
        tf.enable_languages(self.root, ("xx",))
        code, out, _ = run(self.root, "decision-log", "--lang", "xx", "--title", "Nothing here", "--hashes")
        f = fields(out)
        self.assertEqual((code, f["original_exists"], f["document_exists"], f["source_hash"]), (0, "no", "no", "none"))

    def test_lang_without_glossary_or_dir_uses_defaults(self):
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\nlanguages:\n  draft: en\n  translations: [xx]\n", encoding="utf-8")
        f = fields(run(self.root, "decision-log", "--lang", "xx")[1])
        self.assertEqual((f["dir"], f["glossary"], f["glossary_proposed"]), ("ltr", "none", "none"))

    def test_hashes_for_a_type_without_generated_from_prints_no_hash_line(self):
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\ndoc_types:\n  project-plan:\n    generated_from: []\n", encoding="utf-8")
        code, out, _ = run(self.root, "project-plan", "--hashes")
        self.assertEqual(code, 0)
        self.assertNotIn("source_hash", out)

    def test_template_name_that_leaves_the_project_exits_2(self):
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\ndoc_types:\n  decision-log:\n    template: ../x.md\n", encoding="utf-8")
        code, _, err = run(self.root, "decision-log")
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_bad_flag_exits_2(self):
        self.assertEqual(run(self.root, "status-report", "--bogus")[0], 2)
        self.assertEqual(run(self.root)[0], 2)  # the type is required

    def test_help(self):
        self.assertEqual(run(self.root, "--help")[0], 0)

    def test_missing_project_exits_2(self):
        self.assertEqual(run(self.root / "nope", "decision-log")[0], 2)

    def test_stakeholder_update_and_release_notes(self):
        f_su = fields(run(self.root, "stakeholder-update", "2026-03")[1])
        self.assertEqual(f_su["document"], "pmo/documents/2026-03 - Stakeholder update.md")

        f_rn = fields(run(self.root, "release-notes", "2026-03")[1])
        self.assertEqual(f_rn["document"], "pmo/documents/2026-03 - Release notes.md")

        code, out, _ = run(self.root, "release-notes", "2026-03", "--title", "Release notes - api")
        self.assertEqual(code, 0)
        self.assertEqual(fields(out)["document"], "pmo/documents/2026-03 - Release notes - api.md")

        code_bad, _, err = run(self.root, "release-notes", "2026-03", "--title", "bad/title")
        self.assertEqual(code_bad, 2)
        self.assertIn("title", err)

    def test_non_utf8_template_override_exits_2(self):
        tpl = self.root / "pmo/templates/decision-log.md"
        tpl.parent.mkdir(parents=True, exist_ok=True)
        tpl.write_bytes(b"---\ntype: decision-log\n---\n\xe9\n")
        code, _, err = run(self.root, "decision-log")
        self.assertEqual(code, 2)
        self.assertIn("decision-log.md: not UTF-8 text", err)
        self.assertNotIn("Traceback", err)


class WhereTranslations(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_translations_lines_without_lang(self):
        # Without languages block in config
        code, out, _ = run(self.root, "decision-log")
        self.assertEqual(code, 0)
        f = fields(out)
        self.assertEqual(f["translations"], "none")
        self.assertEqual(f["translate"], "in-period")

        # Acme with xx configured
        tf.enable_languages(self.root, ("xx",))
        code, out, _ = run(self.root, "decision-log")
        self.assertEqual(code, 0)
        f = fields(out)
        self.assertEqual(f["translations"], "xx")
        self.assertEqual(f["translate"], "in-period")

    def test_lang_prints_translation_paths(self):
        tf.enable_languages(self.root, ("xx",), block="    glossary: pmo/data/glossary-xx.md\n")
        code, out, _ = run(self.root, "decision-log", "--lang", "xx")
        self.assertEqual(code, 0)
        f = fields(out)
        self.assertEqual(f["document"], "pmo/documents/Decision log.xx.md")
        self.assertEqual(f["original"], "pmo/documents/Decision log.md")
        self.assertEqual(f["original_exists"], "yes")
        self.assertEqual(f["translation_of"], '"Decision log.md"')
        self.assertEqual(f["dir"], "rtl")
        self.assertEqual(f["glossary"], "pmo/data/glossary-xx.md")
        self.assertEqual(f["glossary_proposed"], "pmo/data/glossary-xx.proposed.md")

    def test_lang_hashes_prints_source_hash(self):
        tf.enable_languages(self.root, ("xx",))
        code, out, _ = run(self.root, "decision-log", "--lang", "xx", "--hashes")
        self.assertEqual(code, 0)
        f = fields(out)
        orig_text = (self.root / "pmo/documents/Decision log.md").read_text(encoding="utf-8")
        expected_hash = f'"{pc.body_hash(orig_text)}"'
        self.assertEqual(f["source_hash"], expected_hash)
        self.assertNotIn("source_hashes", f)

    def test_lang_not_configured_exits_2(self):
        code, _, err = run(self.root, "decision-log", "--lang", "xx")
        self.assertEqual(code, 2)
        self.assertIn("translations", err)

    def test_lang_not_allowed_for_type_exits_2(self):
        tf.enable_languages(self.root, ("xx",))
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\ndoc_types:\n  decision-log:\n    translations: []\n", encoding="utf-8")
        code, _, err = run(self.root, "decision-log", "--lang", "xx")
        self.assertEqual(code, 2)
        self.assertIn("translations", err)

    def test_translate_flag_after_close(self):
        tf.enable_languages(self.root, ("xx",))
        cfg_file = self.root / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\ndoc_types:\n  decision-log:\n    translate: after-close\n", encoding="utf-8")
        code, out, _ = run(self.root, "decision-log")
        self.assertEqual(code, 0)
        self.assertEqual(fields(out)["translate"], "after-close")


if __name__ == "__main__":
    unittest.main()
