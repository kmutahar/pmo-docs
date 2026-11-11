"""Tests for stack files and lookup. Run from the repo root: python3 -m unittest discover tests"""
import contextlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/pmo-docs/scripts"))
import docs_audit as da  # noqa: E402
import pmo_common as pc  # noqa: E402

HEADINGS = (
    "Routes, pages or screens",
    "Data models",
    "Permissions and auth",
    "Config and environments",
    "Tests",
    "List the API live",
)


class StackFiles(unittest.TestCase):
    def test_each_shipped_stack_file_has_the_format(self):
        stacks_dir = pc.SKILL / "references" / "stacks"
        files = sorted(stacks_dir.glob("*.md")) if stacks_dir.exists() else []
        for f in files:
            text = f.read_text(encoding="utf-8")
            lines = text.splitlines()
            self.assertTrue(20 <= len(lines) <= 80, f"{f.name} line count {len(lines)} not in 20..80")
            self.assertNotIn("http://", text, f"{f.name} contains http://")
            self.assertNotIn("https://", text, f"{f.name} contains https://")
            self.assertNotIn("{{", text, f"{f.name} contains {{")

            fm, body = pc.split_front_matter(text)
            self.assertIsInstance(fm, dict, f"{f.name} front matter missing")
            ver = fm.get("playbook_version")
            self.assertIsInstance(ver, int, f"{f.name} playbook_version must be int")
            self.assertNotIsInstance(ver, bool, f"{f.name} playbook_version cannot be bool")

            pre_h2 = body.split("##", 1)[0]
            pre_lines = [line.strip() for line in pre_h2.splitlines()]
            self.assertTrue(
                any(line.startswith("Detected by: ") for line in pre_lines),
                f"{f.name} missing 'Detected by: ' before first ##",
            )
            self.assertTrue(
                any(line.startswith("Checked against: ") for line in pre_lines),
                f"{f.name} missing 'Checked against: ' before first ##",
            )

            h1_lines = [line for line in body.splitlines() if line.startswith("# ")]
            self.assertEqual(len(h1_lines), 1, f"{f.name} must have exactly one # heading, found {len(h1_lines)}")

            h2_headings = tuple(line[3:].strip() for line in body.splitlines() if line.startswith("## "))
            self.assertEqual(h2_headings, HEADINGS, f"{f.name} ## headings do not match HEADINGS in order")

    def test_stack_names_are_lowercase_slugs(self):
        stacks_dir = pc.SKILL / "references" / "stacks"
        files = sorted(stacks_dir.glob("*.md")) if stacks_dir.exists() else []
        for f in files:
            self.assertRegex(f.stem, r"^[a-z0-9][a-z0-9-]*$", f"{f.name} stem is not a lowercase slug")

    def test_the_seven_stacks_ship(self):
        stacks_dir = pc.SKILL / "references" / "stacks"
        files = sorted(stacks_dir.glob("*.md")) if stacks_dir.exists() else []
        stems = {f.stem for f in files}
        self.assertEqual(
            stems,
            {"nextjs", "express", "aspnet-core", "spring-boot", "fastapi", "django", "flutter"},
        )


class Lookup(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        shutil.copytree(ROOT / "examples/acme", self.d / "p")
        self.p = self.d / "p"
        self.cfg = pc.load_config(self.p)

    def test_project_stack_file_wins(self):
        proj_stack = self.p / "pmo/playbooks/stacks/express.md"
        proj_stack.parent.mkdir(parents=True, exist_ok=True)
        proj_stack.write_text("# Project Express\n", encoding="utf-8")
        path, source = pc.find_asset(self.p, self.cfg, "playbooks", "stacks/express.md")
        self.assertEqual(source, "project")
        self.assertEqual(path, proj_stack)

    def test_unknown_stack_has_no_default(self):
        path, source = pc.find_asset(self.p, self.cfg, "playbooks", "stacks/cobol.md")
        self.assertEqual(source, "skill")
        self.assertFalse(path.exists())

    def test_bad_names_are_refused(self):
        bad_names = [
            "stacks/../x.md",
            "/etc/x.md",
            "stacks/a/b.md",
            "stacks/Next.js.md",
            "stacks\\express.md",
            "stacks/express",
            "stacks",
        ]
        for bad in bad_names:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    pc.find_asset(self.p, self.cfg, "playbooks", bad)

    def test_symlink_out_of_the_project_is_refused(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        target = outside / "secret.md"
        target.write_text("# Secret\n", encoding="utf-8")

        stacks_dir = self.p / "pmo/playbooks/stacks"
        stacks_dir.mkdir(parents=True, exist_ok=True)
        link = stacks_dir / "evil.md"
        link.symlink_to(target)

        with self.assertRaises(ValueError):
            pc.find_asset(self.p, self.cfg, "playbooks", "stacks/evil.md")


class Override(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        shutil.copytree(ROOT / "examples/acme", self.d / "p")
        self.p = self.d / "p"

    def run_audit(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = da.main(["--project", str(self.p)])
        return code, out.getvalue()

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

