"""Tests for scripts/docs_audit.py on the Acme fixture. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import datetime
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


if __name__ == "__main__":
    unittest.main()
