"""Tests for the step 7 review fixes (config edge cases, refs lists, overdue vocab). Run from the repo root: python3 -m unittest tests.test_step7_fixes"""
import contextlib
import datetime
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "skills/pmo-docs/scripts"))
import docs_audit as da  # noqa: E402
import overdue  # noqa: E402
import pmo_common as pc  # noqa: E402


class Step7(unittest.TestCase):
    def setUp(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        shutil.copytree(ROOT / "examples/acme", d / "p")
        self.p = d / "p"

    def config(self, extra):
        """Deep-merges the YAML `extra` into the project's config."""
        f = self.p / "pmo/config.yaml"
        cfg = pc.yaml.safe_load(f.read_text(encoding="utf-8"))
        f.write_text(pc.yaml.safe_dump(pc.merge(cfg, pc.yaml.safe_load(extra))), encoding="utf-8")

    def load_fails(self, extra):
        self.config(extra)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            pc.load_config(self.p)
        self.assertEqual(cm.exception.code, 2)
        return err.getvalue()

    def test_project_null_is_a_clear_error(self):
        self.p.joinpath("pmo/config.yaml").write_text("schema_version: 2\nproject: null\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            pc.load_config(self.p)
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("project must be a map", err.getvalue())

    def test_glossary_and_names_paths_must_stay_inside(self):
        err = self.load_fails("languages:\n  ar: {glossary: ../outside.md}\n")
        self.assertIn("languages.ar.glossary", err)
        shutil.copy(ROOT / "examples/acme/pmo/config.yaml", self.p / "pmo/config.yaml")
        err = self.load_fails("languages:\n  ar: {names: ../outside.yaml}\n")
        self.assertIn("languages.ar.names", err)

    def test_refs_may_list_several_registers(self):
        self.config("registers:\n  tasks:\n    refs: {related: [risks, issues]}\n")
        cfg = pc.load_config(self.p)
        self.assertIsInstance(da.xref_problems(self.p, cfg), list)

    def test_overdue_accepts_a_severity_vocab_with_extra(self):
        self.config("registers:\n  issues:\n    enums: {severity: {from: issue_severity, extra: [blocker]}}\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = overdue.main(["--project", str(self.p), "--as-of", "2026-03-15"])
        self.assertEqual(code, 0)

    def test_audit_survives_an_unreadable_register_with_a_names_file(self):
        cfg = pc.load_config(self.p)
        names = self.p / "pmo/names.ar.yaml"
        names.write_text("approved:\n  tasks: {}\nproposed: {}\n", encoding="utf-8")
        self.config("languages:\n  ar: {names: pmo/names.ar.yaml}\n")
        (self.p / cfg["paths"]["registers"] / cfg["registers"]["tasks"]["file"]).write_text("- {id: [unclosed\n", encoding="utf-8")
        self.assertIsInstance(da.names_problems(self.p, pc.load_config(self.p)), list)


if __name__ == "__main__":
    unittest.main()
