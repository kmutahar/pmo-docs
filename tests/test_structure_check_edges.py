"""Edge-case tests for scripts/structure_check.py (parsing helpers, declared checks, odd files, CLI paths) on a copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_structure_check_edges"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_structure_check as base  # noqa: E402
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402
import structure_check as sc  # noqa: E402


def main(*args, cwd=None):
    out, err = io.StringIO(), io.StringIO()
    old = os.getcwd()
    if cwd:
        os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = sc.main(list(args))
            except SystemExit as e:
                code = e.code
    finally:
        os.chdir(old)
    return code, out.getvalue() + err.getvalue()


class Helpers(unittest.TestCase):
    def test_sections_ignore_fences_and_comments_and_need_a_space_after_the_hashes(self):
        body = "intro\n# One\ntext\n```\n## fenced\n```\n<!-- ## commented -->\n#NoSpace\n####### seven\n## Two  \n"
        self.assertEqual([(lv, t) for lv, t, _ in sc.sections(body)], [(1, "One"), (2, "Two")])

    def test_sections_of_nothing(self):
        self.assertEqual(sc.sections(""), [])
        self.assertEqual(sc.sections("just text"), [])

    def test_row_cells_with_escaped_pipes_and_no_closing_pipe(self):
        self.assertEqual(sc.row_cells("| a | b |"), ["a", "b"])
        self.assertEqual(sc.row_cells("| a | b"), ["a", "b"])
        self.assertEqual(sc.row_cells(r"| a \| b | c |"), [r"a \| b", "c"])
        self.assertEqual(sc.row_cells(r"| a | b \|"), ["a", r"b \|"])
        self.assertEqual(sc.row_cells("| |  |"), ["", ""])

    def test_tables(self):
        text = "| a | b |\n|:--|--:|\n| 1 | 2 |\n\n| c |\n| not a separator |\n\n| d |\n|---|\n"
        self.assertEqual(sc.tables(text), [(["a", "b"], [["1", "2"]]), (["d"], [])])
        self.assertEqual(sc.tables(""), [])
        self.assertEqual(sc.tables("| a |"), [])

    def test_norm_and_none_rows(self):
        self.assertEqual(sc.norm("  **Foo**   `Bar`_x_ "), "foo barx")
        self.assertEqual(sc.norm("عنوان ✓"), "عنوان ✓")
        for row, want in ((["None", "", ""], True), (["_none._", ""], True), (["*None*"], True), (["None", "x"], False), ([], False), (["", ""], False)):
            self.assertEqual(sc.is_none_row(row), want, row)

    def test_slots(self):
        for title, want in (("{{team}}", True), ("`{{x}}` notes", True), ("{{a}} {{b}}", False if False else True), ("Notes {{x}}", False), ("--", True), ("", True), ("Plain", False), ("عنوان", False)):
            self.assertEqual(sc.is_slot(title), want, title)

    def test_heading_rx(self):
        rx = sc.heading_rx("{{team}} notes")
        self.assertTrue(rx.match(sc.norm("Backend notes")))
        self.assertFalse(rx.match(sc.norm("notes")))
        self.assertTrue(sc.heading_rx("Cost (USD)").match("cost (usd)"))  # regex characters in a title are literal
        self.assertFalse(sc.heading_rx("a.b").match("axb"))

    def test_span_and_data_rows(self):
        dsec = sc.sections("# T\n## A\n| x |\n|---|\n| 1 |\n| None |\n### A1\n| y |\n|---|\n| 2 |\n## B\n| z |\n|---|\n| 3 |\n")
        self.assertIsNone(sc.span(dsec, "missing"))
        sp = sc.span(dsec, "a")  # case-insensitive, includes sub-sections, stops at the next peer
        self.assertEqual([s[1] for s in sp], ["A", "A1"])
        self.assertEqual(sc.data_rows(sp), [["1"], ["2"]])

    def test_duplicate_ids(self):
        t = "| ID |\n|---|\n| T-1 |\n| `T-1` |\n| T-2 |\n| x-1 |\n| X-1 |\n| X-1 |\n| T-3b |\n| T-3b |\n"
        self.assertEqual(sc.duplicate_ids(t), ["T-1", "T-3b", "X-1"])
        self.assertEqual(sc.duplicate_ids("| ID |\n|---|\n| T-1 |\n\n| ID |\n|---|\n| T-1 |\n"), [])  # per table
        self.assertEqual(sc.duplicate_ids("```\n| ID |\n|---|\n| T-1 |\n| T-1 |\n```\n"), [])

    def test_fences_of_both_kinds_are_ignored(self):
        errs, warns = [], []
        body = "# A\n```html\n<!-- example -->\n```\n"
        sc.check_tail(body, body, errs, warns, False)
        self.assertEqual(errs, [])
        self.assertNotIn("not a heading", [t for _, t, _ in sc.sections("# A\n~~~\n# not a heading\n~~~\n## B\n")])
        self.assertEqual([t for _, t, _ in sc.sections("# A\n## Risks ##\n")], ["A", "Risks"])
        self.assertEqual([t for _, t, _ in sc.sections("# A\n## C#\n")], ["A", "C#"])

    def test_duplicate_ids_with_a_project_prefix(self):
        table = "| ID |\n|---|\n| STORY-1 |\n| STORY-1 |\n"
        self.assertEqual(sc.duplicate_ids(table, {"registers": {"stories": {"prefix": "STORY"}}}), ["STORY-1"])
        self.assertEqual(sc.duplicate_ids(table), [])


class Checks(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(REPO / "examples/acme/pmo", self.root / "pmo")
        (self.root / "pmo/templates").mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.root)
        self.cfg = pc.load_config(self.root)

    def tpl(self, text, name="roadmap.md"):
        (self.root / "pmo/templates" / name).write_text(text, encoding="utf-8")

    def check(self, text):
        return sc.check(self.root, self.cfg, text)

    def errs(self, tpl_checks, doc_body="# R\n\n## S\n| A | B |\n|---|---|\n| 1 | 2 |\n"):
        self.tpl("---\ntype: roadmap\nchecks:\n" + tpl_checks + "---\n# R\n\n## S\n| A | B |\n|---|---|\n| 1 | 2 |\n")
        return " | ".join(self.check("---\ntype: roadmap\n---\n" + doc_body)[0])

    def test_empty_text_and_text_without_front_matter_warn_only(self):
        for text in ("", "# T\n", "\r\n"):
            self.assertEqual(self.check(text)[0], [])
            self.assertTrue(self.check(text)[1])

    def test_front_matter_with_unicode_type_is_not_a_doc_type(self):
        self.assertIn("is not a doc type", " ".join(self.check("---\ntype: نوع\n---\n# T\n")[0]))

    def test_template_version_warnings(self):
        self.tpl("---\ntype: roadmap\ntemplate_version: 3\n---\n# R\n")
        self.assertEqual(self.check("---\ntype: roadmap\ntemplate_version: 3\n---\n# R\n"), ([], []))
        self.assertIn("template_version 2 differs from template v3", self.check("---\ntype: roadmap\ntemplate_version: 2\n---\n# R\n")[1][0])
        self.assertIn("no template_version (template is v3)", self.check("---\ntype: roadmap\n---\n# R\n")[1][0])
        self.tpl("---\ntype: roadmap\n---\n# R\n")  # a template without a version asks for none
        self.assertEqual(self.check("---\ntype: roadmap\ntemplate_version: 9\n---\n# R\n"), ([], []))

    def test_two_titles_and_no_title(self):
        self.tpl("---\ntype: roadmap\n---\n# R\n")
        self.assertIn("exactly one `#` title", " ".join(self.check("---\ntype: roadmap\n---\n# A\n# B\n")[0]))
        self.assertIn("exactly one `#` title", " ".join(self.check("---\ntype: roadmap\n---\ntext\n")[0]))

    def test_extra_sections_warning_is_truncated_after_six(self):
        self.tpl("---\ntype: roadmap\n---\n# R\n")
        body = "# R\n" + "".join(f"## E{i}\n" for i in range(8))
        warn = self.check("---\ntype: roadmap\n---\n" + body)[1][0]
        self.assertTrue(warn.startswith("extra sections: E0; E1; E2; E3; E4; E5"), warn)
        self.assertTrue(warn.endswith(" ..."))
        self.assertNotIn("E6", warn)
        self.assertFalse(self.check("---\ntype: roadmap\n---\n# R\n## E1\n## E2\n")[1][0].endswith("..."))

    def test_empty_table_warns_and_a_table_that_is_missing_is_an_error(self):
        self.tpl("---\ntype: roadmap\n---\n# R\n## S\n| A |\n|---|\n| 1 |\n")
        errs, warns = self.check("---\ntype: roadmap\n---\n# R\n## S\n| A |\n|---|\n")
        self.assertEqual(errs, [])
        self.assertIn("`S`: empty table", warns[0])
        self.assertIn("table with columns ['A'] is missing", " ".join(self.check("---\ntype: roadmap\n---\n# R\n## S\ntext\n")[0]))

    def test_table_columns_compare_ignores_case_and_markup(self):
        self.tpl("---\ntype: roadmap\n---\n# R\n## S\n| A | B |\n|---|---|\n| 1 | 2 |\n")
        self.assertEqual(self.check("---\ntype: roadmap\n---\n# R\n## S\n| **a** | `b` |\n|---|---|\n| 1 | 2 |\n")[0], [])
        self.assertIn("should be ['A', 'B']", " ".join(self.check("---\ntype: roadmap\n---\n# R\n## S\n| B | A |\n|---|---|\n| 1 | 2 |\n")[0]))

    def test_headings_in_a_right_to_left_language_match_by_text(self):
        self.tpl("---\ntype: roadmap\n---\n# R\n## الخطة\n")
        self.assertEqual(self.check("---\ntype: roadmap\n---\n# R\n## الخطة\n")[0], [])
        self.assertIn("is missing", " ".join(self.check("---\ntype: roadmap\n---\n# R\n## المخطط\n")[0]))

    def test_front_matter_closed_without_a_trailing_newline_or_in_crlf_counts_as_no_front_matter(self):
        # documents the current behaviour: the check is skipped with a warning, not failed
        self.assertTrue(self.check("---\r\ntype: roadmap\r\n---\r\n# R\r\n")[1])
        self.assertTrue(self.check("---\ntype: roadmap\n---")[1])

    def test_check_kinds(self):
        self.assertIn("unknown kind or missing keys", self.errs("  - {kind: nope}\n"))
        self.assertIn("unknown kind or missing keys", self.errs("  - plain text\n"))
        self.assertIn("unknown kind or missing keys", self.errs("  - {kind: required_cells, section: S}\n"))
        self.assertIn("template check 2", self.errs("  - {kind: required_cells, section: S, columns: [A]}\n  - {kind: equal_count}\n"))
        self.assertEqual(self.errs(""), "")

    def test_required_cells_branches(self):
        c = "  - {kind: required_cells, section: S, columns: [A, B]}\n"
        self.assertEqual(self.errs(c), "")
        self.assertIn("`S`: column `B` missing", self.errs(c, "# R\n\n## S\n| A |\n|---|\n| 1 |\n"))
        self.assertIn("`S`: no table found", self.errs(c, "# R\n\n## S\ntext\n"))
        self.assertIn("row `1`: B empty", self.errs(c, "# R\n\n## S\n| A | B |\n|---|---|\n| 1 |  |\n"))
        self.assertIn("row `?`: A empty", self.errs(c, "# R\n\n## S\n| A | B |\n|---|---|\n|  | 2 |\n"))
        self.assertIn("B empty", self.errs(c, "# R\n\n## S\n| A | B |\n|---|---|\n| 1 |\n"))  # a short row
        self.assertEqual(self.errs(c, "# R\n\n## S\n| A | B |\n|---|---|\n| None |  |\n"), "")
        self.assertIn("section `S` not found", self.errs(c, "# R\n"))

    def test_equal_count_and_listed_have_sections_branches(self):
        ec = "  - {kind: equal_count, rows_in: I, headings_in: E, level: 3}\n"
        body = "# R\n\n## I\n| N |\n|---|\n| 1 |\n| 2 |\n| None |\n\n## E\n### a\n### b\n"
        self.tpl("---\ntype: roadmap\nchecks:\n" + ec + "---\n# R\n## I\n| N |\n|---|\n| 1 |\n## E\n### a\n")
        self.assertEqual(self.check("---\ntype: roadmap\n---\n" + body)[0], [])
        self.assertIn("`I` has 2 rows but `E` has 1 level-3 headings", " ".join(self.check("---\ntype: roadmap\n---\n" + body.replace("### b\n", ""))[0]))
        lh = "  - {kind: listed_have_sections, listed_in: L, sections_in: W, level: 3}\n"
        self.tpl("---\ntype: roadmap\nchecks:\n" + lh + "---\n# R\n## L\n| S |\n|---|\n| x |\n## W\n### {{n}}\n")
        ok = "# R\n## L\n| S |\n|---|\n| Login |\n| |\n## W\n### Login page\n"
        self.assertEqual(self.check("---\ntype: roadmap\n---\n" + ok)[0], [])  # a heading may extend the listed name, and a blank cell is skipped
        self.assertIn("no level-3 heading for `Orders`", " ".join(self.check("---\ntype: roadmap\n---\n" + ok.replace("| |", "| Orders |"))[0]))

    def test_listed_ids_match_at_a_word_edge(self):
        checks = [{"kind": "listed_have_sections", "listed_in": "List", "sections_in": "Detail", "level": 3}]
        body = "# T\n## List\n| ID |\n|---|\n| R-1 |\n## Detail\n### R-10 - other risk\n"
        self.assertEqual(len(sc.run_checks(checks, sc.sections(body))), 1)
        self.assertEqual(sc.run_checks(checks, sc.sections(body.replace("R-10 - other risk", "R-1 - title"))), [])

    def test_wrongly_typed_checks_give_one_error_each(self):
        dsec = sc.sections("# T\n## A\n| I |\n|---|\n| 1 |\n## B\n### one\n")
        bad = (
            {"kind": "required_cells", "section": 5, "columns": ["A"]},
            {"kind": ["x"]},
            {"kind": "required_cells", "section": "S", "columns": "Level"},
            {"kind": "equal_count", "rows_in": "A", "headings_in": "B", "level": "x"},
        )
        for chk in bad:
            errs = sc.run_checks([chk], dsec)
            self.assertEqual(len(errs), 1, (chk, errs))
            self.assertIn("template check", errs[0])
        self.assertEqual(sc.run_checks([{"kind": "equal_count", "rows_in": "A", "headings_in": "B", "level": "3"}], dsec), [])

    def test_unreplaced_placeholders_comments_and_duplicate_ids(self):
        self.tpl("---\ntype: roadmap\n---\n# R\n")
        errs = self.check("---\ntype: roadmap\nperiod: x\n---\n# R\n{{a}}\n<!-- c -->\n| ID |\n|---|\n| T-1 |\n| T-1 |\n")[0]
        self.assertEqual(len(errs), 3, errs)
        many = "".join(f"| T-{i} |\n| T-{i} |\n" for i in range(1, 11))
        dup = [e for e in self.check("---\ntype: roadmap\n---\n# R\n| ID |\n|---|\n" + many)[0] if e.startswith("duplicate IDs")][0]
        self.assertEqual(dup.count("T-"), 8)  # the list stops at eight

    def test_template_that_leaves_the_project_is_an_error(self):
        self.cfg["doc_types"]["roadmap"]["template"] = "../../../x.md"
        self.assertTrue(self.check("---\ntype: roadmap\n---\n# R\n")[0])

    def test_translation_checks_head_title_and_tail_only(self):
        self.tpl("---\ntype: roadmap\ntemplate_version: 2\n---\n# R\n## S\n")
        errs, warns = self.check("---\ntype: roadmap\ntranslation_of: R.md\n---\n# A\n# B\n{{x}}\n")
        self.assertEqual(len(errs), 3, errs)  # the missing key, the two titles, the placeholder
        self.assertIn("no template_version (template is v2)", warns)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(REPO / "examples/acme/pmo", self.root / "pmo")
        (self.root / "pmo/templates").mkdir(exist_ok=True)
        (self.root / "pmo/templates/roadmap.md").write_text(base.TPL, encoding="utf-8")
        self.docs = self.root / "pmo/documents"
        for f in self.docs.glob("*.md"):
            f.unlink()
        self.addCleanup(shutil.rmtree, self.root)

    def test_non_utf8_file_is_an_error_not_a_traceback(self):
        f = self.docs / "Bin.md"
        f.write_bytes(b"---\ntype: roadmap\n---\n\xff\n")
        code, out = main("--project", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("ERROR pmo/documents/Bin.md: not UTF-8 text", out)
        self.assertIn("1 file(s) with structure errors", out)

    def test_non_utf8_template_names_the_template(self):
        (self.root / "pmo/templates/decision-log.md").write_bytes(b"---\ntype: decision-log\n---\n\xe9\n")
        text = (REPO / "examples/acme/pmo/documents/Decision log.md").read_text(encoding="utf-8")
        doc = self.docs / "Decision log.md"
        doc.write_text(text, encoding="utf-8")
        code, out = main("--project", str(self.root), str(doc))
        self.assertEqual(code, 1)
        self.assertIn("template decision-log.md: not UTF-8 text", out)
        self.assertNotIn("Traceback", out)

    def test_files_not_found_and_a_folder_are_errors(self):
        code, out = main("--project", str(self.root), str(self.docs / "no.md"), str(self.docs))
        self.assertEqual(code, 1)
        self.assertIn("2 file(s) with structure errors", out)

    def test_no_documents_is_clean(self):
        code, out = main("--project", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("0 file(s) with structure errors", out)

    def test_missing_documents_folder_is_clean(self):
        shutil.rmtree(self.docs)
        self.assertEqual(main("--project", str(self.root))[0], 0)

    def test_bad_usage_exits_2(self):
        self.assertEqual(main("--project", str(self.root / "nope"))[0], 2)
        self.assertEqual(main("--project", str(self.root), "--nope")[0], 2)
        self.assertEqual(main("--help")[0], 0)

    def test_nested_documents_and_non_markdown_files(self):
        (self.docs / "a/b").mkdir(parents=True)
        (self.docs / "a/b/Roadmap.md").write_text(base.GOOD, encoding="utf-8")
        (self.docs / "notes.txt").write_text("{{x}}", encoding="utf-8")
        code, out = main("--project", str(self.root))
        self.assertEqual(code, 0, out)
        self.assertIn("ok    pmo/documents/a/b/Roadmap.md", out)
        self.assertNotIn("notes.txt", out)

    def test_relative_file_and_a_file_outside_the_project(self):
        (self.docs / "Roadmap.md").write_text(base.GOOD, encoding="utf-8")
        self.assertEqual(main("--project", str(self.root), "pmo/documents/Roadmap.md", cwd=self.root)[0], 0)
        other = self.root.parent / "elsewhere.md"
        other.write_text(base.GOOD, encoding="utf-8")
        self.addCleanup(other.unlink)
        code, out = main("--project", str(self.root), str(other))
        self.assertEqual(code, 0, out)
        self.assertIn(f"ok    {other}", out)

    def test_warnings_alone_exit_0_and_unicode_names_print(self):
        (self.docs / "تقرير.md").write_text("# no front matter\n", encoding="utf-8")
        code, out = main("--project", str(self.root))
        self.assertEqual(code, 0, out)
        self.assertIn("warn  pmo/documents/تقرير.md: no front matter", out)

    def test_bom_document_is_checked_as_its_type(self):
        text = (REPO / "examples/acme/pmo/documents/Decision log.md").read_text(encoding="utf-8")
        (self.docs / "Decision log.md").write_text(text, encoding="utf-8")
        code1, out1 = main("--project", str(self.root))
        (self.docs / "Decision log.md").write_text(chr(0xFEFF) + text, encoding="utf-8")
        code2, out2 = main("--project", str(self.root))
        self.assertNotIn("no front matter", out2)
        self.assertEqual(code1, code2)


if __name__ == "__main__":
    unittest.main()
