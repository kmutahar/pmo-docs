"""Tests for the plugin manifest files. Run from the repo root: python3 -m unittest tests.test_plugin"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((REPO / ".claude-plugin" / name).read_text(encoding="utf-8"))


class Plugin(unittest.TestCase):
    def test_plugin_json(self):
        p = load("plugin.json")
        self.assertEqual(p["name"], "pmo-docs")
        self.assertEqual(p["license"], "MIT")
        self.assertRegex(p["version"], r"^\d+\.\d+\.\d+$")
        for key in ("description", "author", "homepage", "repository"):
            self.assertTrue(p.get(key), key)
        self.assertLessEqual(len(p["description"]), 300)

    def test_marketplace_json(self):
        m = load("marketplace.json")
        self.assertEqual(m["name"], "pmo-docs")
        self.assertEqual(len(m["plugins"]), 1)
        entry = m["plugins"][0]
        self.assertEqual(entry["name"], "pmo-docs")
        self.assertEqual(entry["source"], "./")
        self.assertNotIn("version", entry)  # the version lives only in plugin.json
        self.assertTrue(m.get("owner", {}).get("name"))

    def test_no_forbidden_folders(self):
        for name in ("hooks", "bin", "requirements.txt"):
            self.assertFalse((REPO / name).exists(), name)

    def test_no_private_paths_in_manifests(self):
        for name in ("plugin.json", "marketplace.json"):
            text = (REPO / ".claude-plugin" / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"/home/|@[\w.-]+\.\w+")


class Evals(unittest.TestCase):
    """The eval files are only run by hand (they cost tokens), so check their shape and fixture here."""
    CASES = ("setup-needs-consent", "status-report-from-acme")

    def test_every_case_has_a_prompt_and_unique_graders(self):
        sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
        import pmo_common  # noqa: F401  (puts the vendored PyYAML on the path)
        import yaml
        for case in self.CASES:
            d = REPO / "evals" / case
            self.assertTrue((d / "prompt.md").read_text(encoding="utf-8").strip(), case)
            names = set()
            for g in sorted((d / "graders").glob("*.md")):
                fm = yaml.safe_load(g.read_text(encoding="utf-8").split("---")[1])
                self.assertIn(fm["type"], {"regex", "tool_order", "tool_used", "file_exists", "llm", "baseline"}, g.name)
                names.add(g.stem)
            self.assertGreaterEqual(len(names), 3, case)

    def test_scaffold_builds_a_valid_acme_without_the_draft(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        subprocess.run(["bash", str(REPO / "evals/status-report-from-acme/scaffold.sh")], cwd=tmp, check=True)
        self.assertFalse((tmp / "pmo/documents/2026-03 - Status report.md").exists())
        p = subprocess.run([sys.executable, str(REPO / "skills/pmo-docs/scripts/render_views.py"), "--check"], cwd=tmp, capture_output=True)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
