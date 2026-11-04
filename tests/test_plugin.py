"""Tests for the plugin manifest files. Run from the repo root: python3 -m unittest tests.test_plugin"""
import json
import re
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


if __name__ == "__main__":
    unittest.main()
