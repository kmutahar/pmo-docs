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
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertNotIn("duplicate id T-1", out)
        self.assertIn("actions T-1: id must look like ACT-1", out)

    def test_conflict_markers_reported_with_file_and_line_and_exit_1(self):
        (self.reg / "tasks.yaml").write_text(
            "tasks:\n<<<<<<< HEAD\n  - {id: T-1, title: a}\n=======\n  - {id: T-1, title: b}\n>>>>>>> branch\n",
            encoding="utf-8",
        )
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("pmo/registers/tasks.yaml:2: merge conflict markers; resolve them first (references/git.md, Several writers)", out)

    def test_duplicate_id_reports_all_copies_with_positions_titles_and_hint(self):
        self.append(
            "tasks",
            '  - {id: T-5, title: "Write release notes", status: not-started}\n  - {id: T-5, title: "Fix login timeout", status: not-started}',
        )
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn(
            'duplicate id T-5: pmo/registers/tasks.yaml:6 "Write release notes", pmo/registers/tasks.yaml:7 "Fix login timeout"; run renumber.py',
            out,
        )

    def test_duplicate_id_with_three_copies(self):
        self.append(
            "tasks",
            '  - {id: T-5, title: "First", status: not-started}\n  - {id: T-5, title: "Second", status: not-started}\n  - {id: T-5, title: "Third", status: not-started}',
        )
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn(
            'duplicate id T-5: pmo/registers/tasks.yaml:6 "First", pmo/registers/tasks.yaml:7 "Second", pmo/registers/tasks.yaml:8 "Third"; run renumber.py',
            out,
        )

    def test_duplicate_id_with_text_label(self):
        self.append(
            "actions",
            '  - {id: ACT-3, text: "First action", status: open}\n  - {id: ACT-3, text: "Second action", status: open}',
        )
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn(
            'duplicate id ACT-3: pmo/registers/actions.yaml:4 "First action", pmo/registers/actions.yaml:5 "Second action"; run renumber.py',
            out,
        )

    def test_shared_prefix_exits_2(self):
        (self.root / "pmo/config.yaml").write_text(
            "schema_version: 1\nregisters:\n  tasks: {file: tasks.yaml, view: tasks.md, fields: [id], prefix: T}\n  tests: {file: tests.yaml, view: tests.md, fields: [id], prefix: T}\n",
            encoding="utf-8",
        )
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("registers tasks and tests both use prefix T", out)

    def test_register_out_of_order_renders_in_id_order_and_file_unchanged(self):
        dec_file = self.reg / "decisions.yaml"
        original = (
            "decisions:\n"
            "  - {id: DEC-3, title: Third decision, date: 2026-03-01, status: accepted}\n"
            "  - {id: DEC-1, title: First decision, date: 2026-03-01, status: accepted}\n"
            "  - {id: DEC-2, title: Second decision, date: 2026-03-01, status: accepted}\n"
        )
        dec_file.write_text(original, encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        view_text = (self.views / "decisions.md").read_text(encoding="utf-8")
        dec1_idx = view_text.index("DEC-1")
        dec2_idx = view_text.index("DEC-2")
        dec3_idx = view_text.index("DEC-3")
        self.assertLess(dec1_idx, dec2_idx)
        self.assertLess(dec2_idx, dec3_idx)
        self.assertEqual(dec_file.read_text(encoding="utf-8"), original)

    def test_tasks_view_orders_ties_by_id(self):
        tasks_file = self.reg / "tasks.yaml"
        tasks_content = (
            "tasks:\n"
            "  - {id: T-1, title: Set up staging server, team: platform, group: infra, priority: high, owner: alice, status: in-progress, due: 2026-03-10, period: 2026-03, notes: Overdue on purpose}\n"
            '  - {id: T-4, title: Fourth, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-04-01, period: 2026-03}\n'
            '  - {id: T-2, title: Second, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03}\n'
            '  - {id: T-3, title: Write API outline, team: platform, group: docs, priority: low, owner: alice, status: done, due: 2026-03-05, period: 2026-03, tests: [TST-1]}\n'
        )
        tasks_file.write_text(tasks_content, encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        view_text = (self.views / "tasks.md").read_text(encoding="utf-8")
        t2_idx = view_text.index("T-2")
        t4_idx = view_text.index("T-4")
        self.assertLess(t2_idx, t4_idx)

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
        (self.reg / "tests.yaml").unlink(missing_ok=True)
        (self.reg / "requirements.yaml").unlink(missing_ok=True)
        (self.reg / "issues.yaml").unlink(missing_ok=True)
        (self.reg / "changes.yaml").unlink(missing_ok=True)
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



class RegisterLinks(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        self.views = self.root / "pmo/views"
        self.cfg_file = self.root / "pmo/config.yaml"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def write_config(self, extra):
        cfg = pc.yaml.safe_load(self.cfg_file.read_text(encoding="utf-8")) or {}
        merged = pc.merge(cfg, extra)
        self.cfg_file.write_text(pc.yaml.safe_dump(merged), encoding="utf-8")

    def append(self, name, line):
        with open(self.reg / f"{name}.yaml", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def test_dotted_enum_checks_against_a_config_list(self):
        self.write_config({
            "domain": {"roles": ["lead"]},
            "registers": {"roster": {"enums": {"role": "domain.roles", "origin": "origin"}}},
        })
        code, out = run(self.root, "--check")
        self.assertEqual(code, 1)
        self.assertIn("role 'Project manager' not in ['lead']", out)

        self.write_config({
            "domain": {"roles": ["Project manager", "Platform lead", "Web lead", "admin", "editor", "viewer"]},
        })
        code, out = run(self.root, "--check")
        self.assertEqual(code, 0, out)

        self.write_config({
            "domain": {"roles": []},
        })
        code, out = run(self.root, "--check")
        self.assertEqual(code, 0, out)

    def test_refs_report_an_unknown_id(self):
        self.write_config({
            "registers": {"issues": {"refs": {"related_tasks": "tasks"}}},
        })
        code, out = run(self.root, "--check")
        self.assertEqual(code, 0, out)

        issue_line = "  - {id: I-99, title: Bad task ref, description: none, severity: low, owner: bob, status: open, origin: stated, raised: 2026-03-10, resolved: null, related_tasks: [T-99]}"
        self.append("issues", issue_line)
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("related_tasks 'T-99' is not an id in tasks", out)

        issues_path = self.reg / "issues.yaml"
        lines = issues_path.read_text(encoding="utf-8").splitlines()
        lines[-1] = "  - {id: I-99, title: Empty task ref, description: none, severity: low, owner: bob, status: open, origin: stated, raised: 2026-03-10, resolved: null, related_tasks: []}"
        issues_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

        lines[-1] = "  - {id: I-99, title: Null task ref, description: none, severity: low, owner: bob, status: open, origin: stated, raised: 2026-03-10, resolved: null, related_tasks: null}"
        issues_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

    def test_refs_to_a_missing_register_file_are_skipped(self):
        self.write_config({
            "registers": {"issues": {"refs": {"related_tasks": "tasks"}}},
        })
        (self.reg / "tasks.yaml").unlink()
        (self.views / "tasks.md").unlink()
        code, out = run(self.root, "--check")
        self.assertEqual(code, 0, out)

    def test_refs_config_errors(self):
        self.write_config({
            "registers": {"issues": {"refs": {"related_tasks": "unknown_register"}}},
        })
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("config: registers.issues.refs target `unknown_register` is not a register", out)

    def test_refs_field_missing_from_fields_is_skipped(self):
        # a project that lists its own tasks.fields without `tests` keeps the default tasks.refs {tests: tests}
        cfg = pc.load_config(self.root)
        fields = [f for f in cfg["registers"]["tasks"]["fields"] if f != "tests"]
        self.write_config({"registers": {"tasks": {"fields": fields}}})
        lines = (self.reg / "tasks.yaml").read_text(encoding="utf-8").replace(", tests: [TST-1]", "")
        (self.reg / "tasks.yaml").write_text(lines, encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

    def test_refs_must_be_a_map_of_field_to_register(self):
        for bad in ("tasks", ["tasks"], {"related_tasks": ["tasks"]}):
            self.write_config({"registers": {"issues": {"refs": bad}}})
            code, out = run(self.root)
            self.assertEqual(code, 2, bad)
            self.assertIn("registers.issues.refs must be a map of field to register", out)
            self.assertNotIn("Traceback", out)

    def test_link_fields_of_the_wrong_type_are_reported(self):
        tasks = self.reg / "tasks.yaml"
        tests = self.reg / "tests.yaml"
        tasks_text, tests_text = tasks.read_text(encoding="utf-8"), tests.read_text(encoding="utf-8")
        for bad in ("{TST-1}", "[[TST-1]]", "{a: b}"):
            tasks.write_text(tasks_text.replace("tests: [TST-1]", f"tests: {bad}"), encoding="utf-8")
            tests.write_text(tests_text.replace("task: T-3", f"task: {bad}"), encoding="utf-8")
            p = subprocess.run([sys.executable, str(TOOL), "--project", str(self.root)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 1, bad)
            self.assertNotIn("Traceback", p.stderr)
            self.assertIn("tasks T-3: tests must be an id or a list of ids", p.stdout)
            self.assertIn("tests TST-1: task must be an id or a list of ids", p.stdout)

    def test_domain_and_technical_config_errors(self):
        self.write_config({"technical": {"stacks": ["Next.js"]}})
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("config: technical.stacks", out)

        self.write_config({"technical": {"stacks": []}, "domain": {"roles": "admin"}})
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("config: domain.roles", out)

        self.write_config({"domain": {"roles": [], "lifecycle_entity": ""}})
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("config: domain.lifecycle_entity", out)


class ScheduleConfig(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.defaults = pc.load_config(self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def test_valid_schedule_passes(self):
        cfg = pc.merge(self.defaults, {
            "schedule": [
                {"recipe": "weekly-status", "when": "Mon 08:00"},
                {"recipe": "docs-audit", "when": "1st 09:00"},
            ]
        })
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertEqual(errs, [])

    def test_recipe_from_project_playbook_passes(self):
        pb_dir = self.root / "pmo/playbooks"
        pb_dir.mkdir(parents=True, exist_ok=True)
        (pb_dir / "custom-recipe.md").write_text("# Custom\n", encoding="utf-8")
        cfg = pc.merge(self.defaults, {
            "schedule": [
                {"recipe": "custom-recipe", "when": "Fri 17:00"}
            ]
        })
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertEqual(errs, [])

    def test_unknown_recipe_is_config_error(self):
        cfg = pc.merge(self.defaults, {
            "schedule": [
                {"recipe": "unknown-recipe", "when": "Mon 08:00"}
            ]
        })
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("unknown" in e and "recipe" in e for e in errs), errs)

    def test_missing_when_is_config_error(self):
        cfg = pc.merge(self.defaults, {
            "schedule": [
                {"recipe": "weekly-status"}
            ]
        })
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertTrue(any("when" in e for e in errs), errs)

    def test_schedule_shape_errors(self):
        cfg_str = pc.merge(self.defaults, {"schedule": "not-a-list"})
        errs_str = render_views.config_errors(cfg_str, root=self.root)
        self.assertTrue(any("must be a list" in e for e in errs_str), errs_str)

        cfg_item = pc.merge(self.defaults, {"schedule": ["not-a-map"]})
        errs_item = render_views.config_errors(cfg_item, root=self.root)
        self.assertTrue(any("must be a map" in e for e in errs_item), errs_item)

        cfg_rec = pc.merge(self.defaults, {"schedule": [{"when": "Mon 08:00"}]})
        errs_rec = render_views.config_errors(cfg_rec, root=self.root)
        self.assertTrue(any("needs recipe" in e for e in errs_rec), errs_rec)

    def test_release_notes_cannot_be_scheduled(self):
        cfg = pc.merge(self.defaults, {
            "schedule": [
                {"recipe": "release-notes", "when": "month end"}
            ]
        })
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertIn("config: schedule recipe `release-notes` cannot be scheduled: it needs a person present", errs)

    def test_release_notes_cannot_be_scheduled_even_with_playbook(self):
        pb_dir = self.root / "pmo/playbooks"
        pb_dir.mkdir(parents=True, exist_ok=True)
        (pb_dir / "release-notes.md").write_text("# Release notes\n", encoding="utf-8")
        cfg = pc.merge(self.defaults, {
            "schedule": [
                {"recipe": "release-notes", "when": "month end"}
            ]
        })
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertIn("config: schedule recipe `release-notes` cannot be scheduled: it needs a person present", errs)

    def test_month_start_is_valid_schedule_recipe(self):
        cfg = pc.merge(self.defaults, {
            "schedule": [
                {"recipe": "month-start", "when": "1st 09:00"}
            ]
        })
        errs = render_views.config_errors(cfg, root=self.root)
        self.assertEqual(errs, [])

    def test_schedule_md_known_recipes_and_release_notes_line(self):
        sched_md = (REPO / "skills/pmo-docs/references/schedule.md").read_text(encoding="utf-8")
        known_line = next(ln for ln in sched_md.splitlines() if "Known recipes:" in ln)
        for name in render_views.KNOWN_RECIPES:
            self.assertIn(f"`{name}`", known_line)
        self.assertNotIn("release-notes", known_line)
        rn_lines = [ln for ln in sched_md.splitlines() if "release-notes" in ln]
        self.assertEqual(len(rn_lines), 1)
        self.assertIn("`release-notes` cannot be scheduled: it needs a person present.", rn_lines[0])


class CommittedViews(unittest.TestCase):
    def test_acme_views_are_current(self):
        self.assertEqual(run(REPO / "examples/acme", "--check")[0], 0)


if __name__ == "__main__":
    unittest.main()
