"""Tests for scripts/render_views.py on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_render_views"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "skills/pmo-docs/scripts/render_views.py"
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402



def run(project, *args):
    p = subprocess.run([sys.executable, str(TOOL), "--project", str(project), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


class RenderViews(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        self.views = self.root / "pmo/views"
        for v in self.views.glob("*.md"):  # start with no views; the committed ones are tested below
            v.unlink()

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def append(self, name, line):
        with open(self.reg / f"{name}.yaml", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def test_acme_is_valid_and_renders(self):
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        text = (self.views / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("GENERATED", text)
        self.assertLess(text.index("| high |"), text.index("| medium |"))  # priority_order from config
        self.assertLess(text.index("| medium |"), text.index("| low |"))
        self.assertTrue((self.views / "risks.md").exists())

    def test_origin_is_accepted_on_every_register(self):
        entries = {
            "tasks": "{id: T-90, title: x, status: not-started, origin: proposed}",
            "actions": "{id: ACT-90, text: x, status: open, origin: proposed}",
            "decisions": "{id: DEC-90, title: x, status: proposed, origin: proposed}",
            "changes": "{id: CR-90, title: x, status: proposed, origin: proposed}",
            "meetings": "{id: MTG-90, title: x, origin: proposed}",
            "milestones": "{id: M-90, title: x, status: not-started, origin: proposed}",
            "dependencies": "{id: D-90, text: x, origin: proposed}",
            "teams": "{id: TM-90, heading: x, origin: proposed}",
            "priorities": "{id: P-90, title: x, status: not-started, origin: proposed}",
        }
        for name, line in entries.items():
            self.append(name, "  - " + line)
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

    def test_missing_register_is_not_an_error(self):
        (self.reg / "teams.yaml").unlink()
        (self.reg / "priorities.yaml").unlink()
        self.assertEqual(run(self.root)[0], 0)
        self.assertFalse((self.views / "teams.md").exists())

    def test_bad_enum_date_and_unknown_field(self):
        self.append("tasks", "  - {id: T-9, title: x, status: finished, due: TBD, colour: red}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        for part in ("status 'finished'", "due 'TBD'", "unexpected field 'colour'"):
            self.assertIn(part, out)
        self.assertFalse((self.views / "tasks.md").exists())  # nothing written on errors

    def test_task_priority_must_be_in_priority_order(self):
        self.append("tasks", "  - {id: T-9, title: x, status: open, priority: urgent}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("priority 'urgent'", out)

    def test_impossible_date_is_reported(self):
        self.append("tasks", "  - {id: T-9, title: x, status: done, due: 2026-02-30}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("tasks.yaml: not readable", out)

    def test_priority_and_owner_checks(self):
        self.append("risks", "  - {id: R-9, title: x, probability: huge, owner: zed, status: open}")
        out = run(self.root)[1]
        self.assertIn("probability 'huge'", out)
        self.assertIn("owner 'zed' is not in the roster", out)

    def test_owner_that_is_a_map_is_an_error_not_a_crash(self):
        self.append("risks", "  - {id: R-9, title: x, owner: {name: alice}, status: open}")
        code, out = run(self.root)
        self.assertIn("is not in the roster", out)
        self.assertNotIn("Traceback", out)

    def test_duplicate_id_across_registers(self):
        self.append("actions", "  - {id: T-1, text: x, status: open}")
        self.assertIn("duplicate id T-1", run(self.root)[1])

    def test_multi_line_entry_fails(self):
        self.append("tasks", "  - {id: T-9, title: x,\n      status: done}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("one line", out)

    def test_deterministic(self):
        run(self.root)
        first = {p.name: p.read_bytes() for p in self.views.glob("*.md")}
        run(self.root)
        self.assertEqual(first, {p.name: p.read_bytes() for p in self.views.glob("*.md")})

    def test_check_detects_stale_and_writes_nothing(self):
        code, out = run(self.root, "--check")
        self.assertEqual(code, 1)  # no views yet
        self.assertIn("stale view", out)
        self.assertFalse((self.views / "tasks.md").exists())
        run(self.root)
        self.assertEqual(run(self.root, "--check")[0], 0)
        self.append("tasks", "  - {id: T-9, title: New, status: not-started}")
        self.assertEqual(run(self.root, "--check")[0], 1)

    def test_check_fails_on_validation_error(self):
        run(self.root)
        self.append("tasks", "  - {id: T-9, title: x, status: nope}")
        self.assertEqual(run(self.root, "--check")[0], 1)

    def test_only_the_top_key_may_be_unindented_or_non_entry(self):
        self.append("tasks", "other: 1")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("one line", out)

    def test_task_statuses_come_from_the_registers_enum_and_null_priority_order(self):
        (self.root / "pmo/config.yaml").write_text(
            "schema_version: 1\nvocab: {priority_order: null, my_status: [todo, done]}\nregisters: {tasks: {enums: {status: my_status}}}\n", encoding="utf-8")
        (self.reg / "tasks.yaml").write_text("tasks:\n  - {id: T-1, title: a, status: todo, priority: high}\n", encoding="utf-8")
        self.assertEqual(run(self.root)[0], 0)
        self.assertIn("todo 1, done 0", (self.views / "tasks.md").read_text(encoding="utf-8"))

    def test_register_without_view_or_fields_is_a_clear_error(self):
        (self.root / "pmo/config.yaml").write_text(
            "schema_version: 1\nregisters: {notes: {file: notes.yaml}}\n", encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("register `notes` needs `view`", out)
        self.assertIn("register `notes` needs `fields`", out)

    def test_non_text_id_is_an_error_and_does_not_crash(self):
        self.append("tasks", "  - {id: 5, title: x, status: done}")
        self.append("tasks", "  - {id: [a], title: y, status: done}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("must be text", out)

    def test_view_of_a_removed_register_file(self):
        run(self.root)
        (self.reg / "teams.yaml").unlink()
        code, out = run(self.root, "--check")
        self.assertEqual(code, 1)
        self.assertIn("teams.md (register file is gone)", out)
        self.assertEqual(run(self.root)[0], 0)
        self.assertFalse((self.views / "teams.md").exists())
        self.assertEqual(run(self.root, "--check")[0], 0)

    def test_missing_project_folder(self):
        self.assertEqual(run(self.root / "nope")[0], 2)

    def test_help(self):
        self.assertEqual(run(self.root, "--help")[0], 0)

    def test_catalogue_lists_every_doc_type(self):
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        cat_file = self.views / "catalogue.md"
        self.assertTrue(cat_file.exists())
        text = cat_file.read_text(encoding="utf-8")
        self.assertIn("# Catalogue", text)
        cfg = pc.load_config(self.root)
        doc_types = list(cfg.get("doc_types", {}).keys())
        last_idx = -1
        for dt in doc_types:
            row_match = f"| {dt} |"
            self.assertIn(row_match, text)
            idx = text.index(row_match)
            self.assertGreater(idx, last_idx)
            last_idx = idx

    def test_catalogue_follows_project_config(self):
        with open(self.root / "pmo/config.yaml", "a", encoding="utf-8") as f:
            f.write("doc_types:\n  status-report:\n    when: custom when trigger\n    generator: null\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        text = (self.views / "catalogue.md").read_text(encoding="utf-8")
        self.assertIn("custom when trigger", text)
        for line in text.splitlines():
            if "| status-report |" in line:
                self.assertIn("| agent |", line)
                self.assertIn("| custom when trigger |", line)

    def test_check_reports_stale_catalogue(self):
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertEqual(run(self.root, "--check")[0], 0)
        cat_file = self.views / "catalogue.md"
        cat_file.write_text("corrupted content\n", encoding="utf-8")
        code, out = run(self.root, "--check")
        self.assertEqual(code, 1)
        self.assertIn("catalogue.md", out)

    def test_when_must_be_text(self):
        with open(self.root / "pmo/config.yaml", "a", encoding="utf-8") as f:
            f.write("doc_types:\n  status-report:\n    when: [a]\n")
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("must be text", out)

    def test_done_on_date_error_and_acme_task_valid(self):
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.append("tasks", "  - {id: T-99, title: x, status: done, done_on: '2026-13-01'}")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("done_on '2026-13-01' is not a YYYY-MM-DD date", out)


class LanguageConfig(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.views = self.root / "pmo/views"
        for v in self.views.glob("*.md"):
            v.unlink()
        self.defaults = pc.load_config(self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_valid_config_returns_empty(self):
        errs = render_views.config_errors(self.defaults, root=self.root)
        self.assertEqual(errs, [])
        valid_custom = pc.merge(self.defaults, {
            "languages": {
                "translations": ["xx"],
                "xx": {"label": "XX", "dir": "rtl"}
            }
        })
        self.assertEqual(render_views.config_errors(valid_custom, root=self.root), [])

    def test_bad_dir(self):
        cfg = pc.merge(self.defaults, {"languages": {"en": {"dir": "up"}}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("languages.en.dir `up` must be ltr or rtl" in e for e in errs))

    def test_translation_equal_to_draft(self):
        cfg = pc.merge(self.defaults, {"languages": {"translations": ["en"]}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("languages.translations code `en` cannot be the draft language" in e for e in errs))

    def test_translation_without_block(self):
        cfg = pc.merge(self.defaults, {"languages": {"translations": ["xx"]}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("languages.xx must be a map with label and dir" in e for e in errs))

    def test_non_string_code_mentions_quoting(self):
        cfg = pc.merge(self.defaults, {"languages": {"translations": [False]}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("quote" in e.lower() for e in errs))

    def test_digits_nine_characters(self):
        cfg = pc.merge(self.defaults, {"languages": {"en": {"digits": "123456789"}}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("digits `123456789` must be a string of ten distinct characters" in e for e in errs))

    def test_unknown_connectors_key(self):
        cfg = pc.merge(self.defaults, {"languages": {"en": {"connectors": {"with": "and"}}}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("connectors key `with` must be one of ['and', 'of', 'to']" in e for e in errs))

    def test_glossary_outside_project_or_not_md(self):
        cfg1 = pc.merge(self.defaults, {"languages": {"en": {"glossary": "../glossary.md"}}})
        errs1 = render_views.config_errors(cfg1, root=self.root)
        self.assertTrue(any("must stay inside the project" in e for e in errs1))

        cfg2 = pc.merge(self.defaults, {"languages": {"en": {"glossary": "glossary.txt"}}})
        errs2 = render_views.config_errors(cfg2, root=self.root)
        self.assertTrue(any("must be a string ending in .md" in e for e in errs2))

    def test_translate_sometimes(self):
        cfg = pc.merge(self.defaults, {"doc_types": {"status-report": {"translate": "sometimes"}}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("doc_types.status-report.translate `sometimes` must be in-period or after-close" in e for e in errs))

    def test_type_translations_not_in_languages_translations(self):
        cfg = pc.merge(self.defaults, {"doc_types": {"status-report": {"translations": ["zz"]}}})
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("doc_types.status-report.translations code `zz` not in languages.translations" in e for e in errs))

    def test_cli_exits_2_on_language_error(self):
        with open(self.root / "pmo/config.yaml", "a", encoding="utf-8") as f:
            f.write("languages:\n  draft: xx\n")
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("languages.xx", out)
        self.assertFalse((self.views / "tasks.md").exists())


class Credentials(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.cfg = pc.load_config(self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def check_secret(self, secret):
        data = {"tasks": [{"id": "T-1", "title": "x", "status": "not-started", "notes": secret}]}
        return render_views.validate(data, self.cfg)

    def test_pattern_private_key_header(self):
        secret = "-----" + "BEGIN " + "RSA " + "PRIVATE KEY-----"
        errs = self.check_secret(secret)
        self.assertTrue(any("looks like a credential (private key header)" in e for e in errs))

    def test_pattern_github_token(self):
        secret = "gh" + "p_" + "a" * 36
        errs = self.check_secret(secret)
        self.assertTrue(any("looks like a credential (GitHub token)" in e for e in errs))

    def test_pattern_api_key(self):
        secret = "s" + "k-" + "b" * 30
        errs = self.check_secret(secret)
        self.assertTrue(any("looks like a credential (API key)" in e for e in errs))

    def test_pattern_bearer_token(self):
        secret = "Bear" + "er " + "c" * 25
        errs = self.check_secret(secret)
        self.assertTrue(any("looks like a credential (chat or bearer token)" in e for e in errs))

    def test_pattern_jwt(self):
        secret = "ey" + "Jh" + "a" * 10 + "." + "ey" + "Jb" + "b" * 10 + "." + "c" * 10
        errs = self.check_secret(secret)
        self.assertTrue(any("looks like a credential (JSON web token)" in e for e in errs))

    def test_pattern_url_with_password(self):
        secret = "ht" + "tps://" + "user:pass@" + "local" + "host/api"
        errs = self.check_secret(secret)
        self.assertTrue(any("looks like a credential (URL with a password)" in e for e in errs))

    def test_pattern_password_assignment(self):
        secret = "pass" + "word=" + "secret123"
        errs = self.check_secret(secret)
        self.assertTrue(any("looks like a credential (password or secret assignment)" in e for e in errs))

    def test_pattern_password_after_colon(self):
        for secret in ("pass" + "word: " + "Example-Pa55-zz", "tok" + "en:" + "a1b2c3d4e5"):
            errs = self.check_secret(secret)
            self.assertTrue(any("looks like a credential (password or secret assignment)" in e for e in errs), secret)

    def test_found_in_any_field(self):
        token = "gh" + "p_" + "x" * 25
        d1 = {"tasks": [{"id": "T-1", "title": "t", "status": "not-started", "notes": token}]}
        errs1 = render_views.validate(d1, self.cfg)
        self.assertTrue(any("notes looks like a credential" in e for e in errs1))

        d2 = {"tasks": [{"id": "T-1", "title": "t", "status": "not-started", "x_extra": token}]}
        errs2 = render_views.validate(d2, self.cfg)
        self.assertTrue(any("x_extra looks like a credential" in e for e in errs2))

        d3 = {"tasks": [{"id": "T-1", "title": "t", "status": "not-started", "notes": ["keep", token]}]}
        errs3 = render_views.validate(d3, self.cfg)
        self.assertTrue(any("notes looks like a credential" in e for e in errs3))

    def test_message_never_repeats_the_secret(self):
        secret = "s" + "k-" + "supersecretstring1234567890"
        data = {"tasks": [{"id": "T-42", "title": "t", "status": "not-started", "notes": secret}]}
        errs = render_views.validate(data, self.cfg)
        cred_errs = [e for e in errs if "looks like a credential" in e]
        self.assertTrue(cred_errs)
        for e in cred_errs:
            self.assertNotIn(secret, e)
            self.assertIn("tasks T-42", e)
            self.assertIn("notes", e)

    def test_ordinary_text_is_not_flagged(self):
        phrases = [
            "Rotate the API key before launch",
            "Reset password flow",
            "token refresh fails",
            "Use the secret manager",
            "Meeting at 10:30",
            "Reset password: done",
            "Token: see the vault",
            "Secret: rotated on Friday",
        ]
        for phrase in phrases:
            data = {"tasks": [{"id": "T-1", "title": phrase, "status": "not-started", "notes": phrase}]}
            errs = render_views.validate(data, self.cfg)
            cred_errs = [e for e in errs if "looks like a credential" in e]
            self.assertEqual(cred_errs, [], f"flagged ordinary text: {phrase}")

    def test_cli_exits_1_and_writes_no_views(self):
        views_folder = self.root / "pmo/views"
        for v in views_folder.glob("*.md"):
            v.unlink()
        secret = "gh" + "p_" + "z" * 30
        task_file = self.root / "pmo/registers/tasks.yaml"
        with open(task_file, "a", encoding="utf-8") as f:
            f.write(f'  - {{id: T-99, title: leak, status: not-started, notes: "{secret}"}}\n')
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("looks like a credential", out)
        self.assertNotIn(secret, out)
        self.assertEqual(list(views_folder.glob("*.md")), [])

    def test_acme_still_valid(self):
        data, read_errors = render_views.read_registers(self.root, self.cfg)
        self.assertEqual(read_errors, [])
        errors = render_views.validate(data, self.cfg)
        self.assertEqual(errors, [])



class CommittedViews(unittest.TestCase):
    def test_acme_views_are_current(self):
        self.assertEqual(run(REPO / "examples/acme", "--check")[0], 0)


if __name__ == "__main__":
    unittest.main()
