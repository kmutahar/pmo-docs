"""Edge-case tests for scripts/parity_check.py (helpers, odd files, usage and paths) on a copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_parity_check_edges"""
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_fixture as tf  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import parity_check as pt  # noqa: E402
import pmo_common as pc  # noqa: E402

NO_IDS = re.compile(r"(?!)")


def main(*args, cwd=None):
    out, err = io.StringIO(), io.StringIO()
    old = os.getcwd()
    if cwd:
        os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = pt.main(list(args))
            except SystemExit as e:
                code = e.code
    finally:
        os.chdir(old)
    return code, out.getvalue() + err.getvalue()


class Helpers(unittest.TestCase):
    def test_normalise_with_no_info(self):
        self.assertEqual(pt.normalise("1 2", None), "1 2")
        self.assertEqual(pt.normalise("1 2", {}), "1 2")

    def test_normalise_ignores_digits_of_the_wrong_length_or_type(self):
        for digits in ("123", 5, None, ["0"] * 10):
            self.assertEqual(pt.normalise("5", {"digits": digits}), "5")

    def test_normalise_digits_separators_and_connectors(self):
        info = {"digits": "٠١٢٣٤٥٦٧٨٩", "separators": "٫,"}
        self.assertEqual(pt.normalise("١٢٫٥", info), "12.5")
        self.assertEqual(pt.normalise("3 to 5, 3 of 5, 3 AND 5, 3–5, 3 — 5, 3/5, 3:5", {}), "3~5, 3~5, 3~5, 3~5, 3~5, 3~5, 3~5")
        self.assertEqual(pt.normalise("3 bis 5", {"connectors": {"to": "bis", "x": "", "y": 5}}), "3~5")
        self.assertEqual(pt.normalise("3 bis 5", {"connectors": "bis"}), "3 bis 5")  # only a map of words counts

    def test_numbers(self):
        n = lambda t, info=None: pt.numbers(t, info or {}, NO_IDS)
        self.assertEqual(n(""), [])
        self.assertEqual(n("no digits here"), [])
        self.assertEqual(n("2026-03-15, 3.5, 25%, 4٪"), ["2026~03~15", "3.5", "25", "4"])
        self.assertEqual(n("-5 +5"), ["-5", "+5"])
        self.assertEqual(n("a1b22"), ["1", "22"])

    def test_numbers_remove_ids_first(self):
        rx = pt.id_regex({"registers": {"tasks": {"prefix": "T"}}})
        self.assertEqual(pt.numbers("T-12 costs 5", {}, rx), ["5"])

    def test_id_regex_uses_config_prefixes_longest_first_and_falls_back(self):
        rx = pt.id_regex({"registers": {"a": {"prefix": "X"}, "b": {"prefix": "XY"}, "c": {"prefix": ""}, "d": "text", "e": {}}})
        self.assertEqual(rx.findall("XY-1 X-2 T-3 aX-4"), ["XY-1", "X-2"])
        for cfg in ({}, None, {"registers": {}}, {"registers": {"a": {"prefix": None}}}):
            self.assertEqual(pt.id_regex(cfg).findall("DEC-1 TM-2 ZZ-3"), ["DEC-1", "TM-2"])

    def test_id_regex_matches_next_to_another_script_but_not_a_latin_letter(self):
        rx = pt.id_regex({})
        self.assertEqual(rx.findall("مهمةT-1"), ["T-1"])
        self.assertEqual(rx.findall("aT-1"), [])
        self.assertEqual(rx.findall("T-"), [])

    def test_prefixes_with_regex_characters_are_escaped(self):
        rx = pt.id_regex({"registers": {"a": {"prefix": "A.B"}}})
        self.assertEqual(rx.findall("A.B-1 AxB-2"), ["A.B-1"])

    def test_text_outside_tables(self):
        text = "intro\n| a | b |\n|---|---|\n| 1 | 2 |\nafter\n| lone line |\n"
        self.assertEqual(pt.text_outside_tables(text), "intro\nafter\n| lone line |")
        self.assertEqual(pt.text_outside_tables(""), "")
        self.assertEqual(pt.text_outside_tables("|a|\n|---|"), "")


class Compare(unittest.TestCase):
    def cmp(self, original, translation, info=None, cfg=None):
        return pt.compare(original, translation, info or {}, cfg or {})

    def test_identical_documents_match(self):
        doc = "---\ntype: x\n---\n# T\n\n## A\n| a | b |\n|---|---|\n| 1 | T-1 |\n"
        self.assertEqual(self.cmp(doc, doc), [])

    def test_empty_documents_match(self):
        self.assertEqual(self.cmp("", ""), [])

    def test_front_matter_differences(self):
        o = "---\ntype: x\nperiod: 2026-03\ntemplate_version: 1\n---\n# T\n"
        t = "---\ntype: y\nperiod: 2026-04\ntemplate_version: 2\n---\n# T\n"
        errs = self.cmp(o, t)
        self.assertEqual(len(errs), 3)
        self.assertEqual(self.cmp("---\ntype: x\n---\n# T\n", "---\ntype: x\nperiod: 2026-04\n---\n# T\n"), [])  # the original has no period

    def test_heading_count_difference_also_reports_tables_and_stops(self):
        o = "# T\n## A\n| a |\n|---|\n| 1 |\n"
        t = "# T\n"
        errs = self.cmp(o, t)
        self.assertEqual(len(errs), 2)
        self.assertIn("heading count differs: original has 2, translation has 1", errs[0])
        self.assertIn("total table count differs: original has 1, translation has 0", errs[1])

    def test_table_shapes(self):
        o = "# T\n## A\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n"
        t = "# T\n## A\n| a |\n|---|\n| 1 |\n"
        errs = self.cmp(o, t)
        self.assertIn("column count differs: 1 != 2", " ".join(errs))
        self.assertIn("rows count differs: 1 != 2", " ".join(errs))
        self.assertEqual(len([e for e in errs if "numbers differ" in e]), 0)  # cells are not paired when the shape differs

    def test_table_count_differs_in_a_section(self):
        o = "# T\n## A\n| a |\n|---|\n| 1 |\n"
        t = "# T\n## A\nno table\n"
        self.assertIn("table count differs: original has 1, translation has 0", " ".join(self.cmp(o, t)))

    def test_header_cell_numbers_are_compared(self):
        o = "# T\n## A\n| 2026 |\n|---|\n| x |\n"
        t = "# T\n## A\n| 2027 |\n|---|\n| x |\n"
        self.assertIn("header cell 1: numbers differ: ['2027'] != ['2026']", " ".join(self.cmp(o, t)))

    def test_digits_in_the_translation_language_are_normalised_but_not_the_original(self):
        info = {"digits": "٠١٢٣٤٥٦٧٨٩"}
        o = "# T\n## A\nOn 12 May\n"
        self.assertEqual(self.cmp(o, "# T\n## A\nOn ١٢ May\n", info), [])
        self.assertNotEqual(self.cmp(o, "# T\n## A\nOn ١٣ May\n", info), [])

    def test_ids_in_a_heading_and_text_are_compared(self):
        errs = self.cmp("# T\n## A T-1\ntext\n", "# T\n## A T-2\ntext\n")
        self.assertTrue(any("ids differ" in e for e in errs), errs)

    def test_heading_level_change_names_the_original_heading(self):
        errs = self.cmp("# T\n## A\n", "# T\n### A\n")
        self.assertEqual(errs, ["`A`: heading level 3 differs from original level 2"])

    def test_headings_in_code_fences_and_comments_are_ignored(self):
        self.assertEqual(self.cmp("# T\n```\n# fake\n```\n<!-- # c -->\n", "# T\n"), [])

    def test_crlf_translation_is_compared_like_lf(self):
        o = "# T\n## A\n| a |\n|---|\n| 1 |\n"
        self.assertEqual(self.cmp(o, o.replace("\n", "\r\n")), [])


class Files(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(REPO / "examples/acme", self.root / "acme")
        self.proj = self.root / "acme"
        self.docs = self.proj / "pmo/documents"
        self.orig = (self.docs / "Decision log.md").read_text(encoding="utf-8")
        tf.enable_languages(self.proj, ("xx",))
        self.trans = tf.make_translation(self.orig)
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, name, text):
        f = self.docs / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return f

    def check(self, f):
        return pt.check_translation(self.proj, pc.load_config(self.proj), f)

    def test_file_not_found(self):
        self.assertEqual(self.check(self.docs / "no.md"), [f"file not found: {self.docs / 'no.md'}"])

    def test_translation_file_that_is_not_utf8(self):
        f = self.docs / "Bin.xx.md"
        f.write_bytes(b"---\ntranslation_of: Decision log.md\n---\n\xff\n")
        self.assertEqual(self.check(f), ["not UTF-8 text"])

    def test_original_that_is_not_utf8(self):
        (self.docs / "Bin.md").write_bytes(b"---\ntype: x\n---\n\xff\n")
        f = self.write("Decision log.xx.md", self.trans.replace("translation_of: Decision log.md", "translation_of: Bin.md"))
        self.assertEqual(self.check(f), ["original `Bin.md` is not UTF-8 text"])

    def test_non_utf8_file_in_the_folder_is_skipped_by_the_default_scan(self):
        (self.docs / "Bin.md").write_bytes(b"\xff\xfe")
        code, out = main("--project", str(self.proj))
        self.assertEqual(code, 0, out)

    def test_translation_of_forms(self):
        for target, want in (("../Decision log.md", "leaves paths.documents"), ("/abs/path.md", "leaves paths.documents"),
                             ("sub", "missing"), ("", "no translation_of"), ("[a]", "must be a string"), ("5", "must be a string")):
            f = self.write("Decision log.xx.md", self.trans.replace("translation_of: Decision log.md", f"translation_of: {target or chr(34) * 2}" if target != "5" else "translation_of: 5"))
            (self.docs / "sub").mkdir(exist_ok=True)
            self.assertIn(want, " ".join(self.check(f)), target)

    def test_lang_forms(self):
        for lang, want in (("[xx]", "lang missing"), ('""', "lang missing"), ("yy", "not in config"), ("5", "lang missing")):
            f = self.write("Decision log.xx.md", self.trans.replace("lang: xx", f"lang: {lang}"))
            self.assertIn(want, " ".join(self.check(f)), lang)

    def test_original_in_a_sub_folder_is_found_relative_to_documents(self):
        (self.docs / "sub").mkdir()
        shutil.move(str(self.docs / "Decision log.md"), str(self.docs / "sub/Decision log.md"))
        f = self.write("Decision log.xx.md", self.trans.replace("translation_of: Decision log.md", "translation_of: sub/Decision log.md"))
        self.assertEqual(self.check(f), [])

    def test_main_usage_and_paths(self):
        self.assertEqual(main("--project", str(self.root / "nope"))[0], 2)
        self.assertEqual(main("--project", str(self.proj), "--nope")[0], 2)
        code, out = main("--project", str(self.proj), str(self.docs / "missing.md"))
        self.assertEqual(code, 1)
        self.assertIn("not a file", out)
        self.assertIn("1 file(s) differ", out)

    def test_relative_file_argument_is_resolved_from_the_current_folder(self):
        self.write("Decision log.xx.md", self.trans)
        code, out = main("--project", str(self.proj), "pmo/documents/Decision log.xx.md", cwd=self.proj)
        self.assertEqual(code, 0, out)
        self.assertIn("ok    pmo/documents/Decision log.xx.md", out)

    def test_file_outside_the_project_is_checked_and_named_by_its_full_path(self):
        out_dir = self.root / "elsewhere"
        out_dir.mkdir()
        f = out_dir / "t.md"
        f.write_text(self.trans, encoding="utf-8")
        code, out = main("--project", str(self.proj), str(f))
        self.assertEqual(code, 0, out)
        self.assertIn(f"ok    {f}", out)

    def test_several_files_count_each_difference(self):
        a = self.write("A.xx.md", self.trans)
        b = self.write("B.xx.md", self.trans.replace("lang: xx", "lang: yy"))
        c = self.write("C.xx.md", self.trans.replace("translation_of: Decision log.md", "translation_of: Gone.md"))
        code, out = main("--project", str(self.proj), str(a), str(b), str(c))
        self.assertEqual(code, 1)
        self.assertIn("2 file(s) differ from their originals", out)

    def test_nested_translations_are_found_by_the_default_scan(self):
        self.write("deep/er/Decision log.xx.md", self.trans)  # translation_of is relative to the documents folder, not to the file
        code, out = main("--project", str(self.proj))
        self.assertEqual(code, 0, out)
        self.assertIn("ok    pmo/documents/deep/er/Decision log.xx.md", out)

    def test_missing_documents_folder_checks_nothing(self):
        shutil.rmtree(self.docs)
        code, out = main("--project", str(self.proj))
        self.assertEqual(code, 0, out)
        self.assertIn("0 file(s) differ", out)

    def test_unicode_file_name(self):
        self.write("سجل ✓.xx.md", self.trans)
        code, out = main("--project", str(self.proj))
        self.assertEqual(code, 0, out)
        self.assertIn("سجل ✓.xx.md", out)


if __name__ == "__main__":
    unittest.main()
