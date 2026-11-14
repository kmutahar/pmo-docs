"""Tests for scripts/docs_audit.py on the Acme fixture. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import datetime
import hashlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_fixture as tf  # noqa: E402
sys.path.insert(0, str(ROOT / "skills/pmo-docs/scripts"))
import docs_audit as da  # noqa: E402
import pmo_common as pc  # noqa: E402

AS_OF = "2026-03-15"


class Audit(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        shutil.copytree(ROOT / "examples/acme", self.d / "p")
        self.p = self.d / "p"
        self.docs = self.p / "pmo/documents"

    def run_audit(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = da.main(["--project", str(self.p), "--as-of", AS_OF])
        return code, out.getvalue()

    def finish(self, hashes=None, extra=""):
        cfg = pc.load_config(self.p)
        if hashes is None:
            hashes = {r: da.register_hash(self.p, cfg, r) for r in cfg["doc_types"]["status-report"]["generated_from"]}
        h = "\n".join(f"  {k}: {v}" for k, v in hashes.items())
        (self.docs / "2026-03 - Status report.md").write_text(
            f"---\ntype: status-report\nstatus: finished\nlast_updated: 2026-03-14\n{extra}source_hashes:\n{h}\n---\n# Report\n",
            encoding="utf-8")

    def test_clean_project_exits_0(self):
        self.finish()
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("Total findings: 0", out)

    def test_register_change_makes_finished_document_stale(self):
        self.finish()
        f = self.p / "pmo/registers/risks.yaml"
        f.write_text(f.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("register `risks` changed", out)

    def test_missing_recorded_hash_is_a_finding(self):
        self.finish(hashes={"tasks": da.register_hash(self.p, pc.load_config(self.p), "tasks")})
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("no recorded hash for register `milestones`", out)

    def test_draft_is_not_checked_for_staleness(self):
        code, out = self.run_audit()  # the Acme status report is a draft
        self.assertEqual(code, 0, out)

    def test_draft_behind_its_registers_is_reported(self):
        self.finish()
        dec_log = self.docs / "Decision log.md"
        dec_log.write_text(
            '---\ntype: decision-log\nstatus: draft\nsource_hashes:\n  decisions: "00000000"\n---\n# Decision log\n',
            encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("## Stale", out)
        self.assertIn("draft is behind", out)

        cur_hash = da.register_hash(self.p, pc.load_config(self.p), "decisions")
        dec_log.write_text(
            f'---\ntype: decision-log\nstatus: draft\nsource_hashes:\n  decisions: "{cur_hash}"\n---\n# Decision log\n',
            encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)

        dec_log.write_text(
            '---\ntype: decision-log\nstatus: draft\n---\n# Decision log\n',
            encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)

    def test_front_matter_findings(self):
        (self.docs / "plain.md").write_text("# no front matter\n", encoding="utf-8")
        (self.docs / "odd.md").write_text("---\ntype: nonsense\n---\n", encoding="utf-8")
        (self.docs / "notype.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("`plain.md` - no front matter", out)
        self.assertIn("type `nonsense` is not a doc type", out)
        self.assertIn("`notype.md` - front matter has no `type`", out)

    def test_old_document_uses_stale_days(self):
        self.finish()
        stale = pc.load_config(self.p)["doc_types"]["status-report"]["stale_days"]
        age = (datetime.date.fromisoformat(AS_OF) - datetime.date(2026, 3, 14)).days
        self.assertLess(age, stale)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = da.main(["--project", str(self.p), "--as-of", str(datetime.date(2026, 3, 14) + datetime.timedelta(days=stale + 1))])
        self.assertEqual(code, 1)
        self.assertIn("days old", out.getvalue())

    def test_broken_link(self):
        (self.docs / "Decision log.md").write_text("---\ntype: decision-log\n---\n[x](missing.md) [y](Decision%20log.md)\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("`missing.md`", out)
        self.assertNotIn("Decision%20log.md`", out)

    def test_multibyte_link_is_decoded(self):
        (self.docs / "\u2713 done.md").write_text("---\ntype: decision-log\n---\nx\n", encoding="utf-8")
        (self.docs / "Decision log.md").write_text("---\ntype: decision-log\n---\n[x](%E2%9C%93%20done.md) [y](missing.md)\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertNotIn("%E2%9C%93", out)
        self.assertIn("`missing.md`", out)  # proves link checks ran

    def test_missing_registers_and_documents_folder(self):
        shutil.rmtree(self.p / "pmo/registers")
        self.assertEqual(da.register_hash(self.p, pc.load_config(self.p), "tasks"), "none")
        shutil.rmtree(self.docs)
        code, _ = self.run_audit()
        self.assertEqual(code, 0)

    def test_integer_hash_says_quote_the_hash_not_stale(self):
        self.finish(hashes={"tasks": 12345678, "milestones": "none"})
        out = self.run_audit()[1]
        self.assertIn("quote the hash", out)
        self.assertNotIn("register `tasks` changed", out)

    def test_finished_without_last_updated_and_datetime_stamp(self):
        self.finish()
        f = self.docs / "2026-03 - Status report.md"
        text = f.read_text(encoding="utf-8")
        f.write_text(text.replace("last_updated: 2026-03-14\n", ""), encoding="utf-8")
        self.assertIn("finished but has no `last_updated`", self.run_audit()[1])
        f.write_text(text.replace("2026-03-14", "2026-03-14 10:30:00"), encoding="utf-8")
        self.assertEqual(self.run_audit()[0], 0)

    def test_non_text_type_and_non_map_front_matter_do_not_crash(self):
        (self.docs / "a.md").write_text("---\ntype: [x]\n---\n", encoding="utf-8")
        (self.docs / "b.md").write_text("---\n- a\n---\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("`a.md` - type `['x']` is not a doc type", out)
        self.assertIn("`b.md` - front matter is not valid YAML", out)

    def test_missing_project_is_a_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            da.main(["--project", str(self.d / "nope")])
        self.assertEqual(e.exception.code, 2)

    def test_help(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as e:
            da.main(["--help"])
        self.assertEqual(e.exception.code, 0)

    def test_a_folder_named_like_a_document_is_not_a_crash(self):
        (self.docs / "x.md").mkdir()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, out = self.run_audit()
        self.assertIn(code, (0, 1))
        self.assertIn("# Docs audit", out)
        self.assertNotIn("Traceback", err.getvalue())
        self.assertNotIn("IsADirectoryError", err.getvalue())

    def test_template_drift(self):
        tpl_dir = self.p / "pmo/templates"
        tpl_dir.mkdir(parents=True, exist_ok=True)
        tpl = tpl_dir / "decision-log.md"

        # Up-to-date override: based_on: decision-log@1 -> no drift finding
        tpl.write_text("---\ntype: decision-log\nbased_on: decision-log@1\n---\n# Decision log\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("## Override drift (0)", out)

        # Older version: based_on: decision-log@0 -> finding, exit 1
        tpl.write_text("---\ntype: decision-log\nbased_on: decision-log@0\n---\n# Decision log\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("the default template moved from v0 to v1", out)

        # No based_on -> finding, exit 1
        tpl.write_text("---\ntype: decision-log\n---\n# Decision log\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("no based_on; add based_on: decision-log@1", out)

        # based_on: roadmap@1 in decision-log.md -> finding, exit 1
        tpl.write_text("---\ntype: decision-log\nbased_on: roadmap@1\n---\n# Decision log\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("based_on names roadmap, the default is decision-log", out)

        # Project-only template custom.md -> no finding
        tpl.unlink()
        (tpl_dir / "custom.md").write_text("---\ntype: custom\n---\n# Custom\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("## Override drift (0)", out)

    def test_playbook_drift(self):
        pb_dir = self.p / "pmo/playbooks"
        pb_dir.mkdir(parents=True, exist_ok=True)
        pb = pb_dir / "draft.md"

        # based_on: draft@1 -> no finding
        pb.write_text("---\nplaybook_version: 1\nbased_on: draft@1\n---\nReads: ...\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("## Override drift (0)", out)

        # draft@0 -> finding
        pb.write_text("---\nplaybook_version: 1\nbased_on: draft@0\n---\nReads: ...\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("the default playbook moved from v0 to v1", out)

        # no based_on -> finding
        pb.write_text("---\nplaybook_version: 1\n---\nReads: ...\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("no based_on; add based_on: draft@1", out)

        # pmo/playbooks/stacks/mystack.md with no default -> no finding
        pb.unlink()
        stacks_dir = pb_dir / "stacks"
        stacks_dir.mkdir(parents=True, exist_ok=True)
        (stacks_dir / "mystack.md").write_text("---\nplaybook_version: 1\n---\nReads: ...\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("## Override drift (0)", out)

    def test_new_project_stack_file_is_not_drift(self):
        stacks_dir = self.p / "pmo/playbooks/stacks"
        stacks_dir.mkdir(parents=True, exist_ok=True)
        (stacks_dir / "cobol.md").write_text("---\nplaybook_version: 1\n---\n# COBOL\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("## Override drift (0)", out)

    def test_override_without_based_on_is_drift(self):
        stacks_dir = self.p / "pmo/playbooks/stacks"
        stacks_dir.mkdir(parents=True, exist_ok=True)
        (stacks_dir / "express.md").write_text("---\nplaybook_version: 1\n---\n# Custom Express\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("no based_on; add based_on: stacks/express@1", out)

    def test_override_up_to_date_is_clean(self):
        stacks_dir = self.p / "pmo/playbooks/stacks"
        stacks_dir.mkdir(parents=True, exist_ok=True)
        (stacks_dir / "express.md").write_text("---\nplaybook_version: 1\nbased_on: stacks/express@1\n---\n# Custom Express\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("## Override drift (0)", out)

    def test_override_behind_the_default_is_drift(self):
        stacks_dir = self.p / "pmo/playbooks/stacks"
        stacks_dir.mkdir(parents=True, exist_ok=True)
        (stacks_dir / "express.md").write_text("---\nplaybook_version: 1\nbased_on: stacks/express@0\n---\n# Custom Express\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("the default playbook moved from v0 to v1", out)

    def test_file_that_is_not_utf8_is_a_finding_not_a_traceback(self):
        (self.docs / "Binary.md").write_bytes(b"---\ntype: decision-log\n---\n\xff\xfe\n")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("`Binary.md` - not UTF-8 text", out)

    def test_documents_without_front_matter_or_with_empty_front_matter(self):
        (self.docs / "Plain.md").write_text("# no front matter\n", encoding="utf-8")
        (self.docs / "Empty.md").write_text("---\n\n---\nbody\n", encoding="utf-8")
        out = self.run_audit()[1]
        self.assertIn("`Plain.md` - no front matter", out)
        self.assertIn("`Empty.md` - front matter has no `type`", out)

    def test_old_boundary_is_exclusive_and_future_dates_are_fine(self):
        self.finish()
        stale = pc.load_config(self.p)["doc_types"]["status-report"]["stale_days"]
        stamp = datetime.date(2026, 3, 14)
        for days, want in ((stale, 0), (stale + 1, 1), (-30, 0)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = da.main(["--project", str(self.p), "--as-of", str(stamp + datetime.timedelta(days=days))])
            self.assertEqual(code, want, days)

    def test_old_check_across_a_leap_day(self):
        self.finish()
        f = self.docs / "2026-03 - Status report.md"
        f.write_text(f.read_text(encoding="utf-8").replace("last_updated: 2026-03-14", "last_updated: 2024-02-28"), encoding="utf-8")
        stale = pc.load_config(self.p)["doc_types"]["status-report"]["stale_days"]
        last_ok = datetime.date(2024, 2, 28) + datetime.timedelta(days=stale)
        self.assertEqual(da.audit_file(self.p, pc.load_config(self.p), f, self.docs, last_ok)[0:0], [])
        old = [c for c, _ in da.audit_file(self.p, pc.load_config(self.p), f, self.docs, last_ok + datetime.timedelta(days=1))]
        self.assertIn("old", old)
        self.assertNotIn("old", [c for c, _ in da.audit_file(self.p, pc.load_config(self.p), f, self.docs, last_ok)])

    def test_last_updated_that_is_not_a_date(self):
        self.finish()
        f = self.docs / "2026-03 - Status report.md"
        f.write_text(f.read_text(encoding="utf-8").replace("2026-03-14", "14 March"), encoding="utf-8")
        self.assertIn("last_updated is not a YYYY-MM-DD date", self.run_audit()[1])

    def test_source_hashes_that_is_not_a_map_is_a_finding(self):
        self.finish()
        f = self.docs / "2026-03 - Status report.md"
        f.write_text("---\ntype: status-report\nstatus: finished\nlast_updated: 2026-03-14\nsource_hashes: [a, b]\n---\n# x\n", encoding="utf-8")
        out = self.run_audit()[1]
        self.assertIn("source_hashes must be a map of register to hash", out)

    def test_registers_in_generated_from_that_are_not_configured_are_skipped(self):
        (self.p / "pmo/config.yaml").write_text(
            (self.p / "pmo/config.yaml").read_text(encoding="utf-8") + "\ndoc_types:\n  status-report:\n    generated_from: [no-such-register]\n", encoding="utf-8")
        self.finish(hashes={"no-such-register": "abcd1234"})
        self.assertEqual(self.run_audit()[0], 0)

    def test_link_forms(self):
        (self.docs / "sub").mkdir()
        (self.docs / "sub/Here.md").write_text("---\ntype: decision-log\nstatus: draft\n---\n", encoding="utf-8")
        (self.docs / "Decision log.md").write_text(
            "---\ntype: decision-log\nstatus: draft\n---\n"
            "[a](https://x.test/nope) [b](http://x.test) [c](#section) [d](mailto:someone) [e](sub/Here.md#frag) [f](sub) [g](./sub/Here.md)\n"
            "[h](gone.md) [i](sub/gone.md#frag) [j](Decision%20log.md)\n", encoding="utf-8")
        out = self.run_audit()[1]
        broken = out[out.index("## Broken links"):out.index("## Override drift")]
        self.assertIn("(2)", broken)
        self.assertIn("`gone.md`", broken)
        self.assertIn("`sub/gone.md#frag`", broken)

    def test_links_with_any_url_scheme_and_links_in_code_fences_are_not_checked(self):
        (self.docs / "Decision log.md").write_text(
            "---\ntype: decision-log\nstatus: draft\n---\n"
            "[a](ftp://x.test/f) [b](tel:+100) [c](data:text/plain,hi) [d](file:///x) [e](git+ssh://h/r)\n"
            "```\n[f](in-backticks.md)\n```\n~~~md\n[g](in-tildes.md)\n~~~\n[h](real-gone.md)\n", encoding="utf-8")
        out = self.run_audit()[1]
        broken = out[out.index("## Broken links"):out.index("## Override drift")]
        self.assertIn("`real-gone.md`", broken)
        self.assertIn("(1)", broken)
        for skipped in ("ftp", "tel", "data", "file", "ssh", "backticks", "tildes"):
            self.assertNotIn(skipped, broken)

    def test_link_in_a_nested_document_is_resolved_from_its_own_folder(self):
        (self.docs / "sub").mkdir()
        (self.docs / "sub/A.md").write_text("---\ntype: decision-log\nstatus: draft\n---\n[up](../Decision log.md) [bad](Decision log.md)\n".replace(" log.md)", "%20log.md)"), encoding="utf-8")
        out = self.run_audit()[1]
        self.assertIn("`sub/A.md` -> `Decision%20log.md`", out)
        self.assertNotIn("`../Decision%20log.md`", out)

    def test_only_markdown_files_are_scanned_and_nested_ones_count(self):
        (self.docs / "notes.txt").write_text("no front matter\n", encoding="utf-8")
        (self.docs / "deep/er").mkdir(parents=True)
        (self.docs / "deep/er/X.md").write_text("---\ntype: decision-log\nstatus: draft\n---\n", encoding="utf-8")
        out = self.run_audit()[1]
        self.assertIn("Scanned 3 Markdown files.", out)
        self.assertNotIn("notes.txt", out)

    def test_empty_documents_folder_scans_nothing_and_exits_0(self):
        shutil.rmtree(self.docs)
        self.docs.mkdir()
        code, out = self.run_audit()
        self.assertEqual(code, 0)
        self.assertIn("Scanned 0 Markdown files.", out)

    def test_as_of_must_be_a_real_date(self):
        for bad in ("2026-02-30", "x", ""):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
                da.main(["--project", str(self.p), "--as-of", bad])
            self.assertEqual(e.exception.code, 2)

    def test_template_based_on_malformed_or_newer_than_the_default(self):
        tpl_dir = self.p / "pmo/templates"
        tpl_dir.mkdir(parents=True)
        tpl = tpl_dir / "decision-log.md"
        for based_on, expect in (("decision-log", "is not <type>@<number>"), ("decision-log@x", "is not <type>@<number>"),
                                 ("decision-log@2", "newer than the default (v1)"), ("' '", "is not <type>@<number>"), ("5", "is not <type>@<number>")):
            with self.subTest(based_on=based_on):
                tpl.write_text(f"---\ntype: decision-log\nbased_on: {based_on}\n---\n# x\n", encoding="utf-8")
                self.assertIn(expect, self.run_audit()[1])

    def test_template_and_playbook_that_are_not_utf8_are_drift_not_a_crash(self):
        for sub, name in (("pmo/templates", "decision-log.md"), ("pmo/playbooks", "draft.md")):
            with self.subTest(sub=sub):
                d = self.p / sub
                d.mkdir(parents=True, exist_ok=True)
                (d / name).write_bytes(b"---\ntype: x\n---\n\xff\xfe\n")
                code, out = self.run_audit()
                self.assertEqual(code, 1, out)
                self.assertIn(f"`{name}` - not UTF-8 text", out)
                self.assertNotIn("Traceback", out)
                (d / name).unlink()

    def test_template_and_playbook_folders_that_are_absent_or_unset(self):
        shutil.rmtree(self.p / "pmo/templates", ignore_errors=True)
        cfg = pc.load_config(self.p)
        self.assertEqual((da.template_drift(self.p, cfg), da.playbook_drift(self.p, cfg)), ([], []))
        cfg["paths"]["playbooks"] = None
        self.assertEqual(da.playbook_drift(self.p, cfg), [])

    def test_drift_state(self):
        cfg = pc.load_config(self.p)
        skill_tpl = pc.SKILL / "assets/templates/decision-log.md"
        self.assertEqual(da.drift_state(self.p, cfg, skill_tpl, "skill"), "n/a")
        tpl = self.p / "pmo/templates/decision-log.md"
        tpl.parent.mkdir(parents=True)
        tpl.write_text("---\ntype: decision-log\nbased_on: decision-log@1\n---\n", encoding="utf-8")
        self.assertEqual(da.drift_state(self.p, cfg, tpl, "project"), "no")
        tpl.write_text("---\ntype: decision-log\n---\n", encoding="utf-8")
        self.assertEqual(da.drift_state(self.p, cfg, tpl, "project"), "yes")
        own = tpl.with_name("custom-only.md")
        own.write_text("x\n", encoding="utf-8")
        self.assertEqual(da.drift_state(self.p, cfg, own, "project"), "n/a")

    def test_unicode_document_names_and_content(self):
        (self.docs / "تقرير ✓.md").write_text("---\ntype: decision-log\nstatus: draft\n---\n[x](مفقود.md)\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("`تقرير ✓.md` -> `مفقود.md`", out)

    def test_status_typo_is_a_finding(self):
        f = self.docs / "Decision log.md"
        f.write_text(f.read_text(encoding="utf-8").replace("status: draft", "status: Finished", 1), encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("## Front matter (1)", out)
        self.assertIn("status `Finished` is not draft or finished", out)

    def test_invalid_front_matter_yaml_is_a_finding(self):
        (self.docs / "Decision log.md").write_text("---\ntype: [\n---\n# x\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("## Front matter (1)", out)
        self.assertIn("`Decision log.md` - front matter is not valid YAML", out)

    def test_link_forms_angles_titles_root_and_inline_code(self):
        (self.docs / "2026-03 - Status report.md").write_text(
            "---\ntype: status-report\nstatus: draft\n---\n"
            '[a](<no such file.md>) [b](missing.md "title")\n'
            "[c](/etc/hostname) [d](/docs/guide.md)\n"
            "`[e](in-code.md)` [f](<Decision log.md>)\n",
            encoding="utf-8",
        )
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        broken = out[out.index("## Broken links"):out.index("## Override drift")]
        self.assertIn("(2)", broken)
        self.assertIn("`no such file.md`", broken)
        self.assertIn("`missing.md`", broken)
        for skipped in ("/etc/hostname", "/docs/guide.md", "in-code.md", "Decision log.md"):
            self.assertNotIn(skipped, broken)

    def test_register_hash_ignores_line_endings(self):
        cfg = pc.load_config(self.p)
        reg = self.p / "pmo/registers/tasks.yaml"
        lf_bytes = reg.read_bytes().replace(b"\r\n", b"\n")
        self.assertIn(b"\n", lf_bytes)
        reg.write_bytes(lf_bytes)
        lf_hash = da.register_hash(self.p, cfg, "tasks")
        self.assertEqual(lf_hash, hashlib.sha256(lf_bytes).hexdigest()[:8])
        reg.write_bytes(lf_bytes.replace(b"\n", b"\r\n"))
        crlf_hash = da.register_hash(self.p, cfg, "tasks")
        self.assertEqual(crlf_hash, lf_hash)


class Translations(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        shutil.copytree(ROOT / "examples/acme", self.d / "p")
        self.p = self.d / "p"
        self.docs = self.p / "pmo/documents"

    def run_audit(self, as_of=AS_OF):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = da.main(["--project", str(self.p), "--as-of", as_of])
        return code, out.getvalue()

    def finish_decision_log(self, text=None):
        cfg = pc.load_config(self.p)
        h = da.register_hash(self.p, cfg, "decisions")
        f = self.docs / "Decision log.md"
        base_text = text if text is not None else f.read_text(encoding="utf-8")
        fm, body = pc.split_front_matter(base_text)
        fm = fm or {}
        fm["status"] = "finished"
        fm["last_updated"] = "2026-03-15"
        fm["source_hashes"] = {"decisions": str(h)}
        import yaml
        new_text = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n{body}"
        f.write_text(new_text, encoding="utf-8")
        return f, new_text

    def finish_translation(self, orig_text, lang="xx", dir_="rtl"):
        trans_text = tf.make_translation(orig_text, lang=lang, dir_=dir_)
        fm, body = pc.split_front_matter(trans_text)
        fm["status"] = "finished"
        fm["last_updated"] = "2026-03-15"
        import yaml
        new_text = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n{body}"
        f = self.docs / f"Decision log.{lang}.md"
        f.write_text(new_text, encoding="utf-8")
        return f, new_text

    def test_good_translation_is_clean(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        self.finish_translation(orig_text)
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)
        self.assertIn("Total findings: 0", out)

    def test_translation_behind(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        self.finish_translation(orig_text)

        # Body changed in original
        (self.docs / "Decision log.md").write_text(orig_text.replace("Need cheap hosting", "Need costly hosting"), encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("## Translation behind (1)", out)
        self.assertIn("translation behind its original", out)

        # Comment-only change does not make it behind
        (self.docs / "Decision log.md").write_text(orig_text + "\n<!-- extra comment -->\n", encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 0, out)

    def test_finishing_the_original_does_not_make_it_behind(self):
        tf.enable_languages(self.p, ("xx",))
        draft_orig = (self.docs / "Decision log.md").read_text(encoding="utf-8") + "\n<!-- author note -->\n"
        (self.docs / "Decision log.md").write_text(draft_orig, encoding="utf-8")
        self.finish_translation(draft_orig)

        # Now finish the original (adds finished status and hashes, strips comments)
        self.finish_decision_log()
        code, out = self.run_audit()
        self.assertNotIn("translation behind its original", out)

    def test_parity_findings_are_reported(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans_file, trans_text = self.finish_translation(orig_text)

        bad_trans = "\n".join([ln for ln in trans_text.splitlines() if "DEC-2 |" not in ln])
        trans_file.write_text(bad_trans, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("## Parity (2)", out)
        self.assertIn("Summary", out)

    def test_missing_translation_of_target(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans_text = tf.make_translation(orig_text).replace("translation_of: Decision log.md", "translation_of: Missing.md")
        (self.docs / "Decision log.xx.md").write_text(trans_text, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("translation_of does not name a document", out)

    def test_translation_of_a_translation(self):
        tf.enable_languages(self.p, ("xx", "yy"))
        _, orig_text = self.finish_decision_log()
        self.finish_translation(orig_text, lang="xx")

        trans2 = tf.make_translation(orig_text, lang="yy").replace("translation_of: Decision log.md", "translation_of: Decision log.xx.md")
        (self.docs / "Decision log.yy.md").write_text(trans2, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("the original is itself a translation", out)

    def test_unknown_lang(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans_text = tf.make_translation(orig_text, lang="yy")
        (self.docs / "Decision log.yy.md").write_text(trans_text, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("lang yy is not a translation language in the config", out)

    def test_type_not_translated_into_lang(self):
        tf.enable_languages(self.p, ("xx",))
        cfg_file = self.p / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8") + "\ndoc_types:\n  decision-log:\n    translations: []\n", encoding="utf-8")
        _, orig_text = self.finish_decision_log()
        self.finish_translation(orig_text)
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("type decision-log is not translated into xx", out)

    def test_wrong_file_suffix(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans_text = tf.make_translation(orig_text)
        (self.docs / "Decision log.wrong.md").write_text(trans_text, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("the file name should end in .xx.md", out)

    def test_wrong_dir(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans_text = tf.make_translation(orig_text, dir_="ltr")
        (self.docs / "Decision log.xx.md").write_text(trans_text, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("dir should be rtl", out)

    def test_source_hashes_present(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans_text = tf.make_translation(orig_text).replace("source_hash:", "source_hashes:\n  decisions: 12345678\nsource_hash:")
        (self.docs / "Decision log.xx.md").write_text(trans_text, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("translations record source_hash, not source_hashes", out)

    def test_unquoted_all_digit_source_hash(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans_text = tf.make_translation(orig_text)
        bad_trans = re.sub(r"source_hash:.*", "source_hash: 12345678", trans_text)
        (self.docs / "Decision log.xx.md").write_text(bad_trans, encoding="utf-8")
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("source_hash is missing or not quoted text", out)

    def test_finished_translation_of_draft_original(self):
        tf.enable_languages(self.p, ("xx",))
        orig_text = (self.docs / "Decision log.md").read_text(encoding="utf-8")
        self.finish_translation(orig_text)
        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("finished, but its original is not finished", out)

    def test_register_stale_check_skips_translations(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        self.finish_translation(orig_text)

        # Modify decisions register
        reg = self.p / "pmo/registers/decisions.yaml"
        reg.write_text(reg.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        code, out = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("`Decision log.md` - register `decisions` changed", out)
        self.assertNotIn("Decision log.xx.md` - register", out)

    def test_old_check_skips_translations(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        self.finish_translation(orig_text)

        code, out = self.run_audit(as_of="2030-01-01")
        self.assertEqual(code, 1)
        self.assertIn("`Decision log.md` - ", out)
        self.assertIn("days old", out)
        # Verify Decision log.xx.md is not in ## Old
        old_section = out.split("## Old")[1].split("##")[0]
        self.assertNotIn("Decision log.xx.md", old_section)


    def test_translation_whose_original_is_not_utf8_or_leaves_the_folder(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans = tf.make_translation(orig_text)
        (self.docs / "Bin.md").write_bytes(b"---\ntype: decision-log\n---\n\xff\n")
        (self.docs / "Decision log.xx.md").write_text(trans.replace("translation_of: Decision log.md", "translation_of: Bin.md"), encoding="utf-8")
        self.assertIn("the original is not UTF-8 text", self.run_audit()[1])
        for target in ("../Decision log.md", "/etc/hostname", "sub", ""):
            with self.subTest(target=target):
                (self.docs / "Decision log.xx.md").write_text(trans.replace("translation_of: Decision log.md", f"translation_of: '{target}'"), encoding="utf-8")
                self.assertIn("translation_of does not name a document", self.run_audit()[1])

    def test_translation_with_a_lang_that_is_not_text(self):
        tf.enable_languages(self.p, ("xx",))
        _, orig_text = self.finish_decision_log()
        trans = tf.make_translation(orig_text).replace("lang: xx", "lang: [xx]")
        (self.docs / "Decision log.xx.md").write_text(trans, encoding="utf-8")
        out = self.run_audit()[1]
        self.assertIn("is not a translation language in the config", out)

if __name__ == "__main__":
    unittest.main()
