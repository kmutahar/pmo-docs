"""Tests for project.id_width: padding validation, numeric order past the width, renumber.py --pad, and the upgrade of a schema 1 project. Run from the repo root: python3 -m unittest tests.test_pad_ids"""
import io
import contextlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/pmo-docs/scripts"
FIXTURE = REPO / "tests/fixtures/acme-0.1"  # unpadded ids, schema_version 1
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import pmo_common as pc  # noqa: E402
import renumber  # noqa: E402

DOC = """---
title: Notes
type: x
status: draft
---

# Notes

Task `T-4` blocks R-2 and T-1000; UTF-8 and X-5 stay.

```
T-4 inside a fence stays
```

- see T-12
"""


def run(script, root, *args, stdin=subprocess.DEVNULL):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), "--project", str(root), *args],
                       capture_output=True, text=True, encoding="utf-8", stdin=stdin)
    return p.returncode, p.stdout + p.stderr


class PadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "p"
        shutil.copytree(FIXTURE, self.root)
        (self.root / "pmo/documents").mkdir(parents=True, exist_ok=True)
        (self.root / "pmo/documents/Notes.md").write_text(DOC, encoding="utf-8")
        self.cfg = self.root / "pmo/config.yaml"
        self.tasks = self.root / "pmo/registers/tasks.yaml"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_config(self, schema=2, width=None):
        extra = "" if width is None else f"  id_width: {width}\n"
        self.cfg.write_text(f"schema_version: {schema}\nproject:\n  name: Acme Portal\n  manager: Sam Example\n{extra}", encoding="utf-8")

    def width3(self):
        self.set_config()


class Validation(PadTest):
    def test_schema_1_without_key_is_unpadded(self):
        self.assertEqual(pc.id_width(pc.load_config(self.root)), 0)
        self.assertEqual(run("render_views.py", self.root)[0], 0)

    def test_schema_2_requires_padding(self):
        self.width3()
        self.assertEqual(pc.id_width(pc.load_config(self.root)), 3)
        code, out = run("render_views.py", self.root, "--check")
        self.assertEqual(code, 1, out)
        self.assertIn("T-1 is not padded; use T-001, or run renumber.py --pad", out)

    def test_ref_field_is_checked_too(self):
        self.width3()
        self.tasks.write_text(self.tasks.read_text(encoding="utf-8").replace("{id: T-", "{id: T-00", 1)  # T-001: padded
                              .replace("id: T-2,", "id: T-002,").replace("id: T-3,", "id: T-003,").replace("id: T-4,", "id: T-004,"), encoding="utf-8")
        dep = self.root / "pmo/registers/dependencies.yaml"
        self.assertIn("T-", dep.read_text(encoding="utf-8"))
        code, out = run("render_views.py", self.root, "--check")
        self.assertIn("dependencies", out)
        self.assertIn("is not padded; use T-00", out)

    def test_width_zero_reports_nothing(self):
        self.set_config(2, 0)
        code, out = run("render_views.py", self.root)
        self.assertEqual(code, 0, out)
        self.assertNotIn("not padded", out)

    def test_width_is_a_minimum(self):
        self.assertIsNone(pc.unpadded("T-1000", 3))
        self.assertIsNone(pc.unpadded("T-004", 3))
        self.assertEqual(pc.unpadded("T-4", 3), "T-004")

    def test_bad_width_is_a_config_error(self):
        self.set_config(2, 10)
        code, out = run("render_views.py", self.root)
        self.assertEqual(code, 2)
        self.assertIn("id_width", out)

    def test_numeric_order_past_the_width(self):
        self.width3()
        self.tasks.write_text("tasks:\n"
                              "  - {id: T-1000, title: Later, status: not-started}\n"
                              "  - {id: T-999, title: Earlier, status: not-started}\n", encoding="utf-8")
        for f in (self.root / "pmo/registers").glob("*.yaml"):
            if f != self.tasks and f.name != "roster.yaml":
                f.unlink()
        code, out = run("render_views.py", self.root)
        self.assertEqual(code, 0, out)
        view = (self.root / "pmo/views/tasks.md").read_text(encoding="utf-8")
        self.assertLess(view.index("T-999"), view.index("T-1000"))
        self.assertEqual(sorted(["T-1000", "T-999"], key=pc.id_num), ["T-999", "T-1000"])


class Pad(PadTest):
    def setUp(self):
        super().setUp()
        self.width3()

    def test_yes_pads_everything_and_renders(self):
        code, out = run("renumber.py", self.root, "--pad", "--yes")
        self.assertEqual(code, 0, out)
        self.assertIn("register tasks.yaml: 4", out)
        self.assertIn("{id: T-001,", self.tasks.read_text(encoding="utf-8"))
        self.assertEqual(run("render_views.py", self.root, "--check")[0], 0)
        doc = (self.root / "pmo/documents/Notes.md").read_text(encoding="utf-8")
        self.assertIn("`T-004` blocks R-002 and T-1000; UTF-8 and X-5 stay.", doc)
        self.assertIn("T-4 inside a fence stays", doc)
        self.assertIn("- see T-012", doc)

    def test_second_run_changes_nothing(self):
        run("renumber.py", self.root, "--pad", "--yes")
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        code, out = run("renumber.py", self.root, "--pad", "--yes")
        self.assertEqual(code, 0)
        self.assertIn("no ids to pad", out)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_no_terminal_without_yes_stops(self):
        before = self.tasks.read_text(encoding="utf-8")
        code, out = run("renumber.py", self.root, "--pad")
        self.assertEqual(code, 2)
        self.assertIn("register tasks.yaml: 4", out)  # the summary is the dry run
        self.assertIn("--yes", out)
        self.assertEqual(self.tasks.read_text(encoding="utf-8"), before)

    def _ask(self, answer):
        args = mock.Mock(project=str(self.root), yes=False)
        buf = io.StringIO()
        with mock.patch.object(sys.stdin, "isatty", return_value=True), mock.patch("builtins.input", return_value=answer), \
                contextlib.redirect_stdout(buf):
            return renumber.pad_main(args, pc.load_config(self.root))

    def test_terminal_yes_pads(self):
        self.assertEqual(self._ask("y"), 0)
        self.assertIn("{id: T-001,", self.tasks.read_text(encoding="utf-8"))

    def test_terminal_no_changes_nothing(self):
        before = self.tasks.read_text(encoding="utf-8")
        self.assertEqual(self._ask("n"), 2)
        self.assertEqual(self.tasks.read_text(encoding="utf-8"), before)

    def test_lowering_the_width_needs_no_rewrite(self):
        run("renumber.py", self.root, "--pad", "--yes")
        self.set_config(2, 2)
        self.assertEqual(run("render_views.py", self.root)[0], 0)

    def test_current_finished_document_stays_current(self):
        doc = self.root / "pmo/documents/Decision log.md"
        self.set_config(1)
        run("render_views.py", self.root)
        import docs_audit
        cfg = pc.load_config(self.root)
        old = docs_audit.register_hash(self.root, cfg, "decisions")
        doc.write_text(f'---\ntitle: Decision log\ntype: decision-log\nstatus: finished\nsource_hashes:\n  decisions: "{old}"\n---\n\n# Decision log\n\n| `DEC-1` | x |\n', encoding="utf-8")
        self.width3()
        self.assertEqual(run("renumber.py", self.root, "--pad", "--yes")[0], 0)
        new = docs_audit.register_hash(self.root, pc.load_config(self.root), "decisions")
        self.assertNotEqual(old, new)
        text = doc.read_text(encoding="utf-8")
        self.assertIn(f'decisions: "{new}"', text)
        self.assertIn("`DEC-001`", text)

    def test_pad_updates_names_file_snapshot_and_current_translation(self):
        self.cfg.write_text(
            "schema_version: 2\nproject:\n  name: Acme Portal\n  manager: Sam Example\n"
            "languages:\n  translations: [ar]\n  ar: {label: AR, dir: rtl, names: pmo/data/names-ar.yaml}\n",
            encoding="utf-8",
        )
        names_file = self.root / "pmo/data/names-ar.yaml"
        names_file.parent.mkdir(parents=True, exist_ok=True)
        names_file.write_text("approved:\n  tasks:\n    T-1: {title: عنوان}\n", encoding="utf-8")

        snap_file = self.root / "pmo/snapshots/2026-03-01.json"
        snap_file.parent.mkdir(parents=True, exist_ok=True)
        snap_file.write_text('{"date": "2026-03-01", "entries": {"tasks": {"T-1": "in-progress", "T-2": "not-started"}}}\n', encoding="utf-8")

        orig = self.root / "pmo/documents/Decision log.md"
        orig.write_text("---\ntitle: Decision log\ntype: decision-log\nstatus: finished\n---\n\n# Decision log\n\n| `DEC-1` | x |\n", encoding="utf-8")
        old_body = pc.body_hash(orig.read_text(encoding="utf-8"))
        trans = self.root / "pmo/documents/Decision log.ar.md"
        trans.write_text(
            f'---\ntitle: Decision log\ntype: decision-log\nstatus: finished\nlang: ar\ndir: rtl\ntranslation_of: "Decision log.md"\nsource_hash: "{old_body}"\n---\n\n# Decision log\n\n| `DEC-1` | x |\n',
            encoding="utf-8",
        )

        code, out = run("renumber.py", self.root, "--pad", "--yes")
        self.assertEqual(code, 0, out)
        self.assertIn("snapshots: 2 in 1 files", out)
        self.assertIn("other files: 1 in 1 files", out)

        names_text = names_file.read_text(encoding="utf-8")
        self.assertIn("T-001:", names_text)
        self.assertNotIn("T-1:", names_text)

        snap_text = snap_file.read_text(encoding="utf-8")
        self.assertIn('"T-001"', snap_text)
        self.assertIn('"T-002"', snap_text)

        new_body = pc.body_hash(orig.read_text(encoding="utf-8"))
        self.assertNotEqual(old_body, new_body)
        trans_text = trans.read_text(encoding="utf-8")
        self.assertIn("`DEC-001`", trans_text)
        self.assertIn(f'source_hash: "{new_body}"', trans_text)


    def test_pad_skips_urls_and_decimals_and_warns_on_unclosed_fence(self):
        doc = self.root / "pmo/documents/Notes.md"
        doc.write_text(
            "---\ntitle: Notes\ntype: x\nstatus: draft\n---\n\n# Notes\n\n"
            "See T-4. Also https://example.com/issues/T-4 and version T-1.5 stay.\n\n"
            "```\nT-4 in unclosed fence\n",
            encoding="utf-8",
        )
        code, out = run("renumber.py", self.root, "--pad", "--yes")
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING pmo/documents/Notes.md: unclosed code fence", out)
        text = doc.read_text(encoding="utf-8")
        self.assertIn("See T-004.", text)
        self.assertIn("https://example.com/issues/T-4", text)
        self.assertIn("T-1.5", text)
        self.assertIn("T-4 in unclosed fence", text)

    def test_pad_ends_a_url_at_a_table_pipe_or_bracket(self):
        text, count = renumber.pad_text("|T-4|https://x.example/a|T-5| [l](https://x.example/T-6) T-7", renumber.re.compile(r"\b(T)-([0-9]+)\b"), 3, True)
        self.assertEqual(text, "|T-004|https://x.example/a|T-005| [l](https://x.example/T-6) T-007")
        self.assertEqual(count, 3)


class Upgrade(PadTest):
    def test_migration_pads_and_sets_schema_2(self):
        script = SCRIPTS / "migrate/0001_pad_ids.py"
        p = subprocess.run([sys.executable, str(script), "--project", str(self.root), "--yes"],
                           capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(self.cfg.read_text(encoding="utf-8").startswith("schema_version: 2\n"))
        self.assertEqual(run("render_views.py", self.root, "--check")[0], 0)
        p = subprocess.run([sys.executable, str(script), "--project", str(self.root)], capture_output=True, text=True,
                           encoding="utf-8", stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 0)
        self.assertIn("already 2", p.stdout)

    def test_migration_without_a_yes_changes_nothing(self):
        p = subprocess.run([sys.executable, str(SCRIPTS / "migrate/0001_pad_ids.py"), "--project", str(self.root)],
                           capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 2)
        self.assertTrue(self.cfg.read_text(encoding="utf-8").startswith("schema_version: 1\n"))

    def test_migration_rejects_invalid_config_cleanly(self):
        self.cfg.write_text("schema_version: 1\nproject:\n  name: Acme\n  manager: Sam\nregisters:\n  tasks: bad\n", encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPTS / "migrate/0001_pad_ids.py"), "--project", str(self.root), "--yes"],
                           capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 2)
        self.assertIn("ERROR config:", p.stderr)
        self.assertNotIn("AttributeError", p.stderr)

    def test_migration_preserves_crlf_without_schema_line(self):
        self.cfg.write_bytes(b"project:\r\n  name: Acme Portal\r\n  manager: Sam Example\r\n")
        p = subprocess.run([sys.executable, str(SCRIPTS / "migrate/0001_pad_ids.py"), "--project", str(self.root), "--yes"],
                           capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(self.cfg.read_bytes().startswith(b"schema_version: 2\r\nproject:\r\n"))


if __name__ == "__main__":
    unittest.main()
