"""Tests for scripts/docs_audit.py on the Acme fixture. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import datetime
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
        self.assertIn("`b.md` - front matter has no `type`", out)

    def test_missing_project_is_a_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            da.main(["--project", str(self.d / "nope")])
        self.assertEqual(e.exception.code, 2)

    def test_help(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as e:
            da.main(["--help"])
        self.assertEqual(e.exception.code, 0)

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


if __name__ == "__main__":
    unittest.main()
