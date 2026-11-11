"""Edge tests for scripts/render_views.py (config checks, validation shapes, rendering, exit codes, odd files) on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_render_views_edges"""
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402
import render_views as rv  # noqa: E402


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = rv.main(list(argv))
    except SystemExit as e:
        code = e.code
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"
        self.views = self.root / "pmo/views"
        self.cfg = pc.load_config(self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def errors(self, patch):
        return rv.config_errors(pc.merge(self.cfg, patch), root=self.root)

    def has(self, patch, text):
        errs = self.errors(patch)
        self.assertTrue(any(text in e for e in errs), errs)


class ConfigErrors(Base):
    def test_shared_prefix_is_config_error(self):
        self.has({"registers": {"tests": {"prefix": "T"}}}, "registers tasks and tests both use prefix T")

    def test_domain_not_a_map(self):
        self.has({"domain": ["x"]}, "domain must be a map")

    def test_domain_lifecycle_entity_null_is_fine(self):
        self.assertEqual(self.errors({"domain": {"lifecycle_entity": None}}), [])

    def test_domain_lifecycle_entity_must_be_text(self):
        self.has({"domain": {"lifecycle_entity": 5}}, "domain.lifecycle_entity")
        self.has({"domain": {"lifecycle_entity": "  "}}, "domain.lifecycle_entity")

    def test_domain_roles_shapes(self):
        self.assertEqual(self.errors({"domain": {"roles": []}}), [])
        self.has({"domain": {"roles": [1]}}, "domain.roles")
        self.has({"domain": {"roles": ["a", " "]}}, "domain.roles")

    def test_technical_shapes(self):
        self.has({"technical": "x"}, "technical must be a map")
        self.has({"technical": {"stacks": "x"}}, "technical.stacks must be a list")
        self.has({"technical": {"stacks": ["Upper"]}}, "must match [a-z0-9]")
        self.has({"technical": {"stacks": ["-x"]}}, "must match [a-z0-9]")
        self.assertEqual(self.errors({"technical": {"stacks": ["next-js", "go1"]}}), [])
        self.has({"technical": {"consumers": "x"}}, "technical.consumers must be a list")
        self.has({"technical": {"consumers": [""]}}, "technical.consumers must be a list")

    def test_publish_mode_and_shape(self):
        self.has({"publish": "x"}, "publish must be a map")
        self.has({"publish": {"mode": "ftp"}}, "publish.mode `ftp`")
        for mode in ("none", "folder", "repo", None):
            self.assertEqual(self.errors({"publish": {"mode": mode}}), [])

    def test_week_start_must_be_a_weekday(self):
        self.has({"project": {"week_start": "funday"}}, "project.week_start")
        self.has({"project": {"week_start": 1}}, "project.week_start")
        self.assertEqual(self.errors({"project": {"week_start": "SUNDAY"}}), [])

    def test_blocked_active_done_statuses_checked_against_vocab(self):
        self.has({"registers": {"tasks": {"blocked": ["nope"]}}}, "registers.tasks.blocked status `nope`")
        self.has({"registers": {"tasks": {"active": ["nope"]}}}, "registers.tasks.active status `nope`")
        self.has({"registers": {"tasks": {"done": ["nope"]}}}, "registers.tasks.done status `nope`")
        self.has({"registers": {"changes": {"accepted": ["nope"]}}}, "registers.changes.accepted status `nope`")

    def test_register_must_be_a_map(self):
        self.has({"registers": {"risks": "x"}}, "register `risks` needs `file`")

    def test_refs_target_not_a_register(self):
        self.has({"registers": {"tasks": {"refs": {"risk": "nowhere"}}}}, "`nowhere` is not a register")

    def test_doc_type_when_regenerate_must_be_text(self):
        self.has({"doc_types": {"status-report": {"regenerate": 3}}}, "doc_types.status-report.regenerate must be text")

    def test_doc_type_translate_and_translations(self):
        self.has({"doc_types": {"status-report": {"translate": "never"}}}, "translate `never`")
        self.has({"doc_types": {"status-report": {"translations": "xx"}}}, "translations must be a list")
        self.has({"doc_types": {"status-report": {"translations": ["zz"]}}}, "code `zz` not in languages.translations")
        self.has({"doc_types": {"status-report": {"translations": [5]}}}, "code `5` not in languages.translations")
        for ok in ("in-period", "after-close"):
            self.assertEqual(self.errors({"doc_types": {"status-report": {"translate": ok}}}), [])

    def test_non_map_doc_type_is_ignored_by_checks(self):
        self.assertEqual(self.errors({"doc_types": {"odd": "text"}}), [])

    def test_languages_shapes(self):
        self.has({"languages": ["x"]}, "languages must be a map")
        self.has({"languages": {"draft": True}}, "languages.draft `True` must be text")
        self.has({"languages": {"draft": "EN!"}}, "languages.draft `EN!` must match")
        self.has({"languages": {"translations": "xx"}}, "languages.translations must be a list")
        self.has({"languages": {"translations": [True]}}, "must be text")
        self.has({"languages": {"translations": ["X!"]}}, "must match")

    def test_languages_translations_duplicate(self):
        self.has({"languages": {"translations": ["xx", "xx"], "xx": {"label": "X", "dir": "ltr"}}}, "duplicate code `xx`")

    def test_language_block_needs_label_and_dir(self):
        self.has({"languages": {"translations": ["xx"], "xx": "text"}}, "languages.xx must be a map")
        self.has({"languages": {"translations": ["xx"], "xx": {"label": " ", "dir": "ltr"}}}, "languages.xx.label")
        self.has({"languages": {"translations": ["xx"], "xx": {"label": "X"}}}, "languages.xx.dir `None`")

    def test_language_digits(self):
        base = {"label": "X", "dir": "ltr"}
        for bad in ("123", "1123456789", "01234567890", 5):
            self.has({"languages": {"translations": ["xx"], "xx": {**base, "digits": bad}}}, "digits")
        good = "٠١٢٣٤٥٦٧٨٩"
        self.assertEqual(self.errors({"languages": {"translations": ["xx"], "xx": {**base, "digits": good}}}), [])

    def test_language_connectors(self):
        base = {"label": "X", "dir": "ltr"}
        self.has({"languages": {"translations": ["xx"], "xx": {**base, "connectors": "x"}}}, "connectors must be a map")
        self.has({"languages": {"translations": ["xx"], "xx": {**base, "connectors": {"or": "o"}}}}, "connectors key `or`")
        self.has({"languages": {"translations": ["xx"], "xx": {**base, "connectors": {"of": " "}}}}, "connectors.of")
        self.assertEqual(self.errors({"languages": {"translations": ["xx"], "xx": {**base, "connectors": {"of": "ﻣﻦ", "and": "و"}}}}), [])

    def test_language_separators_and_glossary(self):
        base = {"label": "X", "dir": "ltr"}
        self.has({"languages": {"translations": ["xx"], "xx": {**base, "separators": 5}}}, "separators must be text")
        self.has({"languages": {"translations": ["xx"], "xx": {**base, "glossary": "g.txt"}}}, "glossary `g.txt`")
        self.has({"languages": {"translations": ["xx"], "xx": {**base, "glossary": "../g.md"}}}, "must stay inside the project")
        self.has({"languages": {"translations": ["xx"], "xx": {**base, "glossary": 5}}}, "glossary `5`")

    def test_glossary_path_is_not_checked_without_a_root(self):
        cfg = pc.merge(self.cfg, {"languages": {"translations": ["xx"], "xx": {"label": "X", "dir": "ltr", "glossary": "../g.md"}}})
        self.assertEqual(rv.config_errors(cfg), [])

    def test_schedule_without_root_skips_playbook_lookup(self):
        cfg = pc.merge(self.cfg, {"schedule": [{"recipe": "weekly-status", "when": "Mondays"}]})
        self.assertEqual(rv.config_errors(cfg), [])


class Helpers(Base):
    def test_real_date(self):
        import datetime
        self.assertTrue(rv.real_date("2028-02-29"))
        self.assertFalse(rv.real_date("2027-02-29"))
        self.assertTrue(rv.real_date(datetime.date(2026, 1, 1)))
        self.assertFalse(rv.real_date("2026-1-1"))
        self.assertFalse(rv.real_date("٢٠٢٦-٠١-٠١"))  # \d would match these; fullmatch then fromisoformat rejects
        self.assertFalse(rv.real_date(None))
        self.assertFalse(rv.real_date(20260101))

    def test_one_line_entries(self):
        self.assertTrue(rv.one_line_entries("risks:\n  - {id: R-1}\n# c\n\n  - {id: R-2}\n"))
        self.assertTrue(rv.one_line_entries(""))
        self.assertFalse(rv.one_line_entries("risks:\n  - {id: R-1,\n    title: x}\n"))

    def test_entry_lines(self):
        text = "# Top comment\n\ntasks:\n\n  # Inner comment\n  - {id: T-1, title: a}\n\n  - {id: T-2, title: b}\n# Trailing\n"
        self.assertEqual(rv.entry_lines(text), [6, 8])
        self.assertEqual(rv.entry_lines(""), [])
        self.assertEqual(rv.entry_lines("tasks:\n# only comments\n"), [])

    def test_id_num(self):
        self.assertEqual(rv._id_num("T-12"), 12)
        self.assertEqual(rv._id_num("none"), 0)
        self.assertEqual(rv._id_num(7), 7)

    def test_allowed(self):
        self.assertEqual(rv.allowed(self.cfg, "no_such_vocab"), [])
        self.assertEqual(rv.allowed(self.cfg, "task_status"), self.cfg["vocab"]["task_status"])
        self.assertEqual(rv.allowed(self.cfg, "domain.nothing.here"), [])
        self.assertEqual(rv.allowed(self.cfg, "project.name"), [])  # a dotted path that is text, not a list

    def test_credential_labels_walks_lists_maps_and_ignores_non_text(self):
        key = "ghp_" + "a" * 24
        self.assertEqual(rv.credential_labels(5), [])
        self.assertEqual(rv.credential_labels(None), [])
        self.assertEqual(rv.credential_labels([[key]]), ["GitHub token"])
        self.assertEqual(rv.credential_labels({"k": {"v": key}}), ["GitHub token"])
        self.assertEqual(rv.credential_labels({key: 1}), ["GitHub token"])
        self.assertEqual(rv.credential_labels({1: "fine"}), [])
        self.assertEqual(rv.credential_labels(("x", key)), ["GitHub token"])

    def test_credential_patterns_near_misses(self):
        self.assertEqual(rv.credential_labels("sk-short"), [])
        self.assertEqual(rv.credential_labels("ghp_short"), [])
        self.assertEqual(rv.credential_labels("Bearer abc"), [])
        self.assertEqual(rv.credential_labels("see https://example.org/a@b"), [])
        self.assertEqual(rv.credential_labels("AKIA" + "A" * 16), ["API key"])
        self.assertEqual(rv.credential_labels("-----BEGIN RSA PRIVATE KEY-----"), ["private key header"])
        self.assertEqual(rv.credential_labels("pwd = x"), ["password or secret assignment"])
        self.assertEqual(rv.credential_labels("xoxb-" + "1" * 12), ["chat or bearer token"])

    def test_linked_tests_shapes(self):
        data = {"tasks": [{"id": "T-1", "tests": ["TS-1", "TS-ghost", {"a": 1}]}, {"id": "T-2", "tests": "TS-2"}, {"id": "T-3", "tests": None}],
                "tests": [{"id": "TS-1"}, {"id": "TS-2", "task": ["T-3"]}, {"id": 9, "task": "T-1"}, {"task": "T-1"}, {"id": ["x"], "task": "T-1"}]}
        self.assertEqual(rv.linked_tests(data, "T-1"), ["TS-1", 9])
        self.assertEqual(rv.linked_tests(data, "T-2"), ["TS-2"])
        self.assertEqual(rv.linked_tests(data, "T-3"), ["TS-2"])
        self.assertEqual(rv.linked_tests(data, 5), [])
        self.assertEqual(rv.linked_tests(data, None), [])
        self.assertEqual(rv.linked_tests({}, "T-1"), [])

    def test_done_without_test_rules(self):
        done = self.cfg["registers"]["tasks"]["done"][0]
        data = {"tasks": [{"id": "T-2", "status": done}, {"id": "T-10", "status": done}, {"id": "T-3", "status": done}, {"id": 4, "status": done}, {"status": done}, {"id": "T-5", "status": "x"}],
                "tests": [{"id": "TS-1", "task": "T-3"}]}
        self.assertEqual(rv.done_without_test(self.cfg, data), ["T-2", "T-10"])
        self.assertEqual(rv.done_without_test(self.cfg, {"tasks": data["tasks"], "tests": []}), [])
        self.assertEqual(rv.done_without_test(self.cfg, {"tasks": data["tasks"]}), [])

    def test_table_empty(self):
        self.assertEqual(rv.table([], ["id"]), "_No entries._\n")


class Rendering(Base):
    def test_view_tasks_empty_has_no_division_error(self):
        text = rv.view_tasks([], self.cfg)
        self.assertIn("0/0 closed (0%)", text)
        self.assertNotIn("Done without", text)

    def test_view_tasks_missing_none_and_list(self):
        self.assertIn("**Done without a linked test:** none", rv.view_tasks([], self.cfg, missing=[]))
        self.assertIn("**Done without a linked test:** T-1, T-2", rv.view_tasks([], self.cfg, missing=["T-1", "T-2"]))

    def test_view_tasks_no_team_group_priority_and_unicode_and_pipe(self):
        rows = [{"id": "T-1", "title": "مهمة | pipe", "status": "not-started"}, {"id": "T-2", "title": "ünï", "status": "not-started", "team": "A", "group": "g", "priority": "high"}]
        text = rv.view_tasks(rows, self.cfg)
        self.assertIn("### no team", text)
        self.assertIn("**no group**", text)
        self.assertIn("not set", text)
        self.assertIn("مهمة", text)
        self.assertNotIn("مهمة | pipe", text)  # the pipe is escaped by md_table
        self.assertIn("ünï", text)

    def test_view_tasks_unknown_priority_sorts_after_known(self):
        rows = [{"id": "T-1", "status": "not-started", "priority": "zzz"}, {"id": "T-2", "status": "not-started", "priority": None}, {"id": "T-3", "status": "not-started", "priority": self.cfg["vocab"]["priority_order"][0]}]
        text = rv.view_tasks(rows, self.cfg).split("## By team")[0]
        self.assertLess(text.index(self.cfg["vocab"]["priority_order"][0]), text.index("zzz"))
        self.assertLess(text.index("zzz"), text.index("not set"))

    def test_render_catalogue_variants(self):
        cfg = pc.merge(self.cfg, {"doc_types": {"a": {"title": None, "stale_days": 0, "publish": False, "generator": True, "when": "", "regenerate": None}, "b": "text", "c": {"generator": "yes"}}})
        views = rv.render({}, cfg)
        cat = views["catalogue.md"]
        a = next(ln for ln in cat.splitlines() if ln.startswith("| a |"))
        self.assertEqual([c.strip() for c in a.strip("|").split("|")], ["a", "not set", "generator", "not set", "not set", "0 days", "no"])
        c = next(ln for ln in cat.splitlines() if ln.startswith("| c |"))
        self.assertIn("| agent |", c)  # generator must be exactly true
        self.assertNotIn("| b |", cat)  # a non-map entry is skipped

    def test_render_no_doc_types_gives_header_only_table(self):
        cfg = dict(self.cfg, doc_types=None)
        self.assertIn("# Catalogue", rv.render({}, cfg)["catalogue.md"])

    def test_render_uses_register_view_names_and_header(self):
        data = {"risks": []}
        views = rv.render(data, self.cfg)
        reg = self.cfg["registers"]["risks"]
        self.assertTrue(views[reg["view"]].startswith("<!-- GENERATED by render_views.py from pmo/registers/" + reg["file"]))
        self.assertIn("_No entries._", views[reg["view"]])


class Validate(Base):
    def check(self, name, rows, extra=None):
        data = {name: rows, **(extra or {})}
        return rv.validate(data, self.cfg)

    def test_missing_id_and_non_text_id(self):
        errs = self.check("risks", [{"title": "x"}, {"id": 5, "title": "y"}, {"id": ["R-1"], "title": "z"}])
        self.assertTrue(any("missing id" in e for e in errs), errs)
        self.assertTrue(any("must be text" in e for e in errs), errs)

    def test_id_prefix_shape(self):
        prefix = self.cfg["registers"]["risks"]["prefix"]
        errs = self.check("risks", [{"id": f"{prefix}-x", "title": "a"}, {"id": f"{prefix}-1", "title": "b"}, {"id": f"{prefix}-01", "title": "c"}])
        self.assertEqual(sum("id must look like" in e for e in errs), 1, errs)

    def test_duplicate_id_in_one_register(self):
        prefix = self.cfg["registers"]["risks"]["prefix"]
        errs = self.check("risks", [{"id": f"{prefix}-1"}, {"id": f"{prefix}-1"}])
        self.assertTrue(any("duplicate id" in e for e in errs), errs)

    def test_validate_without_root_reports_entry_positions(self):
        errs = rv.validate({"tasks": [{"id": "T-1", "title": "A"}, {"id": "T-1", "title": "B"}]}, self.cfg)
        self.assertTrue(any('duplicate id T-1: tasks entry 1 "A", tasks entry 2 "B"; run renumber.py' in e for e in errs), errs)

    def test_x_fields_are_allowed_and_credentials_still_checked(self):
        prefix = self.cfg["registers"]["risks"]["prefix"]
        self.assertEqual(self.check("risks", [{"id": f"{prefix}-1", "status": "open", "x_note": "hi"}]), [])
        errs = self.check("risks", [{"id": f"{prefix}-1", "status": "open", "x_note": "ghp_" + "b" * 24}])
        self.assertTrue(any("looks like a credential" in e for e in errs), errs)

    def test_enum_null_allowed_except_status_and_lists_checked(self):
        t = [{"id": "T-1", "title": "a", "status": None}]
        errs = self.check("tasks", t)
        self.assertTrue(any("status None" in e for e in errs), errs)
        t = [{"id": "T-1", "title": "a", "status": "not-started", "priority": None}]
        self.assertEqual(self.check("tasks", t), [])

    def test_owner_list_checked_against_roster(self):
        slug = self.cfg and rv.pc.yaml.safe_load((self.reg / "roster.yaml").read_text(encoding="utf-8"))["roster"][0]["slug"]
        roster = [{"id": "P-1", "slug": slug}] if "id" in self.cfg["registers"]["roster"]["fields"] else [{"slug": slug}]
        ok = self.check("tasks", [{"id": "T-1", "status": "not-started", "owner": [slug]}], {"roster": roster})
        self.assertEqual([e for e in ok if "owner" in e], [])
        bad = self.check("tasks", [{"id": "T-1", "status": "not-started", "owner": [slug, "nobody"]}], {"roster": roster})
        self.assertTrue(any("'nobody' is not in the roster" in e for e in bad), bad)

    def test_owner_not_checked_without_roster_entries(self):
        errs = self.check("tasks", [{"id": "T-1", "status": "not-started", "owner": "anyone"}])
        self.assertEqual([e for e in errs if "roster" in e], [])

    def test_ref_to_empty_string_and_none_is_skipped_and_dict_reported(self):
        refs = self.cfg["registers"]["tasks"].get("refs") or {}
        if not refs:
            self.skipTest("acme tasks declare no refs")
        field = next(iter(refs))
        rows = [{"id": "T-1", "status": "not-started", field: ""}, {"id": "T-2", "status": "not-started", field: None}, {"id": "T-3", "status": "not-started", field: {"a": 1}}]
        errs = self.check("tasks", rows, {refs[field]: []})
        self.assertEqual(sum("must be an id or a list of ids" in e for e in errs), 1, errs)


class Files(Base):
    def write_reg(self, name, text):
        (self.reg / f"{name}.yaml").write_text(text, encoding="utf-8")

    def test_non_utf8_register_exits_1_with_message_and_writes_nothing(self):
        (self.reg / "risks.yaml").write_bytes(b"risks:\n  - {id: R-1, title: \xff\xfe}\n")
        before = sorted(p.name for p in self.views.glob("*"))
        mtimes = {p.name: p.stat().st_mtime_ns for p in self.views.glob("*")}
        code, out, err = cli("--project", str(self.root))
        self.assertEqual(code, 1, (out, err))
        self.assertIn("risks.yaml: not readable", out)
        self.assertNotIn("Traceback", out + err)
        self.assertEqual(sorted(p.name for p in self.views.glob("*")), before)
        self.assertEqual({p.name: p.stat().st_mtime_ns for p in self.views.glob("*")}, mtimes)

    def test_non_utf8_register_with_check_exits_1(self):
        (self.reg / "risks.yaml").write_bytes(b"risks:\n  - \xff\n")
        code, out, _ = cli("--project", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn("not readable", out)

    def test_views_folder_that_is_a_file_exits_2(self):
        shutil.rmtree(self.views)
        self.views.write_text("not a folder", encoding="utf-8")
        code, out, err = cli("--project", str(self.root))
        self.assertEqual(code, 2, (out, err))
        self.assertIn("cannot write the views folder", err)
        self.assertEqual(self.views.read_text(encoding="utf-8"), "not a folder")

    def test_views_folder_is_created_when_missing_including_parents(self):
        shutil.rmtree(self.views)
        cfg = self.root / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8") + "paths:\n  views: pmo/deep/er/views\n", encoding="utf-8")
        code, out, err = cli("--project", str(self.root))
        self.assertEqual(code, 0, (out, err))
        self.assertTrue((self.root / "pmo/deep/er/views/tasks.md").exists())

    def test_empty_register_file_renders_no_entries(self):
        self.write_reg("risks", "")
        code, out, _ = cli("--project", str(self.root))
        self.assertEqual(code, 0, out)
        self.assertIn("_No entries._", (self.views / self.cfg["registers"]["risks"]["view"]).read_text(encoding="utf-8"))

    def test_register_with_null_list_and_empty_list(self):
        self.write_reg("risks", "risks:\n")
        self.assertEqual(cli("--project", str(self.root))[0], 0)
        self.write_reg("risks", "risks: []\n")
        self.assertEqual(cli("--project", str(self.root))[0], 0)

    def test_register_that_is_a_list_or_text_is_an_error_not_a_crash(self):
        for text in ("- a\n- b\n", "just text\n", "risks: 5\n", "risks:\n  - text\n"):
            self.write_reg("risks", text)
            code, out, err = cli("--project", str(self.root))
            self.assertEqual(code, 1, (text, out, err))
            self.assertNotIn("Traceback", out + err)

    def test_register_with_impossible_yaml_date_is_an_error(self):
        self.write_reg("risks", "risks:\n  - {id: R-1, raised: 2026-02-30}\n")
        code, out, _ = cli("--project", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("risks.yaml: not readable", out)

    def test_register_with_only_comments_and_blank_lines(self):
        self.write_reg("risks", "# nothing yet\n\n")
        self.assertEqual(cli("--project", str(self.root))[0], 0)

    def test_unicode_and_rtl_entries_render(self):
        prefix = self.cfg["registers"]["risks"]["prefix"]
        fields = self.cfg["registers"]["risks"]["fields"]
        title = "مخاطرة ← «ünï»"
        self.write_reg("risks", f"risks:\n  - {{id: {prefix}-1, status: open, title: \"{title}\"}}\n" if "title" in fields else "risks: []\n")
        code, out, _ = cli("--project", str(self.root))
        self.assertEqual(code, 0, out)
        if "title" in fields:
            self.assertIn(title, (self.views / self.cfg["registers"]["risks"]["view"]).read_text(encoding="utf-8"))

    def test_views_are_written_utf8_with_lf(self):
        self.assertEqual(cli("--project", str(self.root))[0], 0)
        raw = (self.views / "catalogue.md").read_bytes()
        self.assertNotIn(b"\r\n", raw)
        raw.decode("utf-8")

    def test_second_run_is_a_no_op_for_content(self):
        cli("--project", str(self.root))
        first = {p.name: p.read_bytes() for p in self.views.glob("*.md")}
        cli("--project", str(self.root))
        self.assertEqual(first, {p.name: p.read_bytes() for p in self.views.glob("*.md")})

    def test_orphan_view_is_removed_on_write_and_reported_by_check(self):
        cli("--project", str(self.root))
        view = self.cfg["registers"]["risks"]["view"]
        (self.reg / "risks.yaml").unlink()
        code, out, _ = cli("--project", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn("register file is gone", out)
        self.assertTrue((self.views / view).exists())
        self.assertEqual(cli("--project", str(self.root))[0], 0)
        self.assertFalse((self.views / view).exists())

    def test_check_with_missing_views_reports_each_as_stale(self):
        shutil.rmtree(self.views)
        code, out, _ = cli("--project", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn("stale view: pmo/views/catalogue.md", out)
        self.assertFalse(self.views.exists())

    def test_check_passes_after_a_write(self):
        cli("--project", str(self.root))
        code, out, _ = cli("--project", str(self.root), "--check")
        self.assertEqual((code, out.strip()), (0, "registers valid, views current"))

    def test_check_on_validation_error_does_not_report_stale(self):
        (self.reg / "risks.yaml").write_text("risks:\n  - {id: bad, title: x}\n", encoding="utf-8")
        code, out, _ = cli("--project", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertNotIn("stale view", out)

    def test_config_error_exits_2_before_reading_registers(self):
        cfg = self.root / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8") + "publish:\n  mode: ftp\n", encoding="utf-8")
        (self.reg / "risks.yaml").write_bytes(b"\xff")
        code, out, _ = cli("--project", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("ERROR config: publish.mode", out)
        self.assertNotIn("not readable", out)

    def test_schedule_recipe_from_a_playbook_file(self):
        pb = self.root / "pmo/playbooks"
        pb.mkdir(parents=True, exist_ok=True)
        (pb / "my-recipe.md").write_text("x\n", encoding="utf-8")
        cfg = pc.merge(self.cfg, {"schedule": [{"recipe": "my-recipe", "when": "Fridays"}]})
        self.assertEqual(rv.config_errors(cfg, root=self.root), [])
        (pb / "my-recipe.md").unlink()
        self.assertTrue(any("`my-recipe` is unknown" in e for e in rv.config_errors(cfg, root=self.root)))

    def test_schedule_entry_shapes(self):
        for entry, text in (("x", "must be a map"), ({"when": "w"}, "needs recipe"), ({"recipe": 5, "when": "w"}, "needs recipe"), ({"recipe": "docs-audit"}, "needs when"), ({"recipe": "docs-audit", "when": 3}, "needs when")):
            errs = rv.config_errors(pc.merge(self.cfg, {"schedule": [entry]}), root=self.root)
            self.assertTrue(any(text in e for e in errs), (entry, errs))


class Cli(Base):
    def test_unknown_flag_and_extra_arg_exit_2(self):
        self.assertEqual(cli("--project", str(self.root), "--nope")[0], 2)
        self.assertEqual(cli("--project", str(self.root), "extra")[0], 2)

    def test_project_flag_needs_a_value(self):
        self.assertEqual(cli("--project")[0], 2)

    def test_project_that_is_a_file_exits_2(self):
        f = self.root / "pmo/config.yaml"
        code, _, err = cli("--project", str(f))
        self.assertEqual(code, 2)
        self.assertIn("project folder not found", err)

    def test_help_exits_0_and_names_check(self):
        code, out, _ = cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("--check", out)

    def test_project_without_config_uses_defaults_or_exits_cleanly(self):
        empty = self.root.parent / "empty"
        empty.mkdir()
        code, out, err = cli("--project", str(empty))
        self.assertIn(code, (0, 1, 2))
        self.assertNotIn("Traceback", out + err)


if __name__ == "__main__":
    unittest.main()
