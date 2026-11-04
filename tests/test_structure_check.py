"""Tests for scripts/structure_check.py on a copy of examples/acme. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402
import structure_check as sc  # noqa: E402

TPL = """---
type: roadmap
template_version: 2
period: "{{period}}"
checks:
  - {kind: required_cells, section: Milestones, columns: [Owner, Due]}
  - {kind: equal_count, rows_in: Index, headings_in: Entries, level: 4}
  - {kind: listed_have_sections, listed_in: Screens, sections_in: Walkthrough, level: 3}
---
# Roadmap {{period}}

## Milestones
| ID | Owner | Due |
|---|---|---|
| M-001 | a | b |

## Index
| N | Name |
|---|---|
| 1 | x |

## Entries
### Group
#### One

## Screens
| Screen |
|---|
| Login |

## Walkthrough
### Login

## {{team}} notes
"""
GOOD = """---
type: roadmap
template_version: 2
period: 2026-03
---
# Roadmap 2026-03

## Milestones
| ID | Owner | Due |
|---|---|---|
| M-001 | sam | 2026-04-01 |
| None | | |

## Index
| N | Name |
|---|---|
| 1 | x |

## Entries
### Group
#### One

## Screens
| Screen |
|---|
| Login |
| Orders |

## Walkthrough
### Login
### Orders (list)

## Backend notes
"""


class StructureCheck(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(REPO / "examples/acme/pmo", self.root / "pmo")
        (self.root / "pmo/templates").mkdir(exist_ok=True)
        (self.root / "pmo/templates/roadmap.md").write_text(TPL, encoding="utf-8")
        self.addCleanup(shutil.rmtree, self.root)
        self.cfg = pc.load_config(self.root)

    def run_check(self, text):
        return sc.check(self.root, self.cfg, text)

    def errs(self, text):
        return " | ".join(self.run_check(text)[0])

    def test_good_document_is_clean(self):
        self.assertEqual(self.run_check(GOOD), ([], []))

    def test_checks_come_from_template_not_draft(self):
        # a draft that declares no checks (or its own lenient ones) is still held to the template's
        bad = GOOD.replace("| sam | 2026-04-01 |", "| | 2026-04-01 |").replace("template_version: 2\n", "template_version: 2\nchecks: []\n")
        self.assertIn("Owner empty", self.errs(bad))

    def test_required_cells_and_none_row(self):
        self.assertIn("row `M-001`: Owner empty", self.errs(GOOD.replace("sam", "")))
        self.assertIn("column `Due` missing", self.errs(GOOD.replace("| ID | Owner | Due |", "| ID | Owner | Date |", 1)))

    def test_equal_count(self):
        self.assertIn("has 2 rows but `Entries` has 1", self.errs(GOOD.replace("| 1 | x |", "| 1 | x |\n| 2 | y |")))

    def test_listed_have_sections(self):
        self.assertIn("no level-3 heading for `Orders`", self.errs(GOOD.replace("### Orders (list)\n", "")))

    def test_check_naming_missing_section_fails(self):
        e = self.errs(GOOD.replace("## Index", "## Renamed index"))
        self.assertIn("section `Index` not found", e)
        self.assertIn("heading `## Index` is missing", e)

    def test_bad_template_check_is_reported(self):
        (self.root / "pmo/templates/roadmap.md").write_text(TPL.replace("kind: equal_count", "kind: nope"), encoding="utf-8")
        self.assertIn("unknown kind", self.errs(GOOD))

    def test_missing_template(self):
        self.cfg["doc_types"]["roadmap"]["template"] = "no-such-template.md"
        self.assertIn("template no-such-template.md not found", self.errs(GOOD))

    def test_front_matter_basics(self):
        self.assertIn("type `nope` is not a doc type", self.errs(GOOD.replace("type: roadmap", "type: nope")))
        self.assertIn("key `period` missing", self.errs(GOOD.replace("period: 2026-03\n", "")))
        self.assertIn("not valid YAML", self.errs("---\nperiod: {{x}}\n---\n# t\n"))
        self.assertEqual(self.run_check("# plain\n")[0], [])
        self.assertIn("template_version 1 differs", " ".join(self.run_check(GOOD.replace("version: 2", "version: 1"))[1]))

    def test_headings_order_columns_leftovers(self):
        idx, ent = "## Index\n| N | Name |\n|---|---|\n| 1 | x |\n\n", "## Entries\n### Group\n#### One\n\n"
        self.assertIn("heading `## Entries` is out of order", self.errs(GOOD.replace(idx + ent, ent + idx)))
        self.assertIn("table columns", self.errs(GOOD.replace("| N | Name |", "| N | Title |")))
        self.assertIn("{{placeholder}}", self.errs(GOOD + "\n{{todo}}\n"))
        self.assertIn("HTML comment", self.errs(GOOD + "\n<!-- note -->\n"))
        self.assertIn("duplicate IDs in one table: M-001", self.errs(GOOD.replace("| None | | |", "| M-001 | a | b |")))

    def test_invalid_template_front_matter_is_an_error(self):
        (self.root / "pmo/templates/roadmap.md").write_text("---\nperiod: {{x}}\n---\n# t\n", encoding="utf-8")
        self.assertIn("template front matter invalid", self.errs(GOOD))

    def test_placeholder_in_front_matter_is_found_and_fences_are_ignored(self):
        self.assertIn("{{placeholder}}", self.errs(GOOD.replace("period: 2026-03", 'period: "{{period}}"')))
        self.assertNotIn("{{placeholder}}", self.errs(GOOD + "\n```\n{{ok}}\n```\n"))

    def test_front_matter_that_is_not_a_map_or_has_non_text_type(self):
        self.assertIn("not valid YAML", self.errs("---\n- a\n- b\n---\n# t\n"))
        self.assertIn("is not a doc type", self.errs(GOOD.replace("type: roadmap", "type: [roadmap]")))

    def test_missing_project_is_a_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            sc.main(["--project", str(self.root / "nope")])
        self.assertEqual(cm.exception.code, 2)

    def test_cli_exit_codes(self):
        d = self.root / "pmo/documents"
        (d / "Roadmap.md").write_text(GOOD, encoding="utf-8")
        for f in d.glob("*.md"):
            if f.name != "Roadmap.md":
                f.unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sc.main(["--project", str(self.root)]), 0)
            (d / "Roadmap.md").write_text(GOOD + "<!-- x -->\n", encoding="utf-8")
            self.assertEqual(sc.main(["--project", str(self.root)]), 1)
            with self.assertRaises(SystemExit) as cm:
                sc.main(["--help"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
