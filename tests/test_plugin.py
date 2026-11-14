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
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common  # noqa: E402


PATHS = {"plugin.json": REPO / "skills/pmo-docs/.claude-plugin/plugin.json", "marketplace.json": REPO / ".claude-plugin/marketplace.json"}


def load(name):
    return json.loads(PATHS[name].read_text(encoding="utf-8"))


class Plugin(unittest.TestCase):
    def test_plugin_json(self):
        p = load("plugin.json")
        self.assertEqual(p["name"], "pmo-docs")
        self.assertEqual(p["license"], "MIT")
        self.assertRegex(p["version"], r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
        for key in ("description", "author", "homepage", "repository"):
            self.assertTrue(p.get(key), key)
        self.assertLessEqual(len(p["description"]), 300)
        for key in ("displayName", "documentationUrl", "supportUrl", "privacyPolicyUrl", "termsOfServiceUrl"):
            self.assertTrue(p.get(key), key)  # the Anthropic directory asks for these
        for key in ("privacyPolicyUrl", "termsOfServiceUrl"):
            self.assertTrue((REPO / p[key].rsplit("/", 1)[1]).is_file(), key)

    def test_skill_and_plugin_versions_agree(self):
        sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts/_vendor"))
        import yaml
        text = (REPO / "skills/pmo-docs/SKILL.md").read_text(encoding="utf-8")
        fm = yaml.safe_load(re.match(r"---\n(.*?)\n---\n", text, re.S).group(1))
        self.assertEqual(str(fm["metadata"]["version"]), load("plugin.json")["version"])

    def test_marketplace_json(self):
        m = load("marketplace.json")
        self.assertEqual(m["name"], "pmo-docs")
        self.assertEqual(len(m["plugins"]), 1)
        entry = m["plugins"][0]
        self.assertEqual(entry["name"], "pmo-docs")
        self.assertEqual(entry["source"], "./skills/pmo-docs")  # only the skill folder is installed, not dev/ or tests/
        self.assertNotIn("version", entry)  # the version lives only in plugin.json
        self.assertTrue(m.get("owner", {}).get("name"))

    def test_plugin_json_points_at_the_skill_folder(self):
        self.assertEqual(load("plugin.json")["skills"], ["./"])

    def test_icon_is_a_square_png_in_the_size_range(self):
        import struct
        data = (REPO / "skills/pmo-docs/.claude-plugin/icon.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        w, h = struct.unpack(">II", data[16:24])  # IHDR width and height
        self.assertEqual(w, h)
        self.assertTrue(512 <= w <= 2048, w)
        self.assertLess(len(data), 2 * 1024 * 1024)

    def test_no_forbidden_folders(self):
        for name in ("hooks", "bin", "requirements.txt"):
            self.assertFalse((REPO / name).exists(), name)

    def test_no_private_paths_in_manifests(self):
        for name in ("plugin.json", "marketplace.json"):
            text = PATHS[name].read_text(encoding="utf-8")
            self.assertNotRegex(text, r"/home/|@[\w.-]+\.\w+")

    def test_command_skills_are_user_only(self):
        skills = sorted((REPO / "skills/pmo-docs/skills").glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skills), 2)
        for path in skills:
            with self.subTest(path.parent.name):
                fm, _ = pmo_common.split_front_matter(path.read_text(encoding="utf-8"), strict=True)
                self.assertIs(fm.get("disable-model-invocation"), True)
                self.assertEqual(fm.get("name"), path.parent.name)

    def test_main_skill_is_not_user_only(self):
        fm, _ = pmo_common.split_front_matter((REPO / "skills/pmo-docs/SKILL.md").read_text(encoding="utf-8"), strict=True)
        self.assertNotIn("disable-model-invocation", fm)


class Evals(unittest.TestCase):
    """The eval files are only run by hand (they cost tokens), so check their shape and fixture here."""

    @staticmethod
    def _grader_front_matter(path):
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])

    def test_every_case_has_a_prompt_and_unique_graders(self):
        import yaml
        prompts = sorted((REPO / "evals").glob("*/prompt.md"))
        self.assertGreaterEqual(len(prompts), 2)
        for prompt in prompts:
            d = prompt.parent
            case = d.name
            if (d / "case.yaml").exists():  # setup-needs-consent has none
                self.assertTrue((d / "scaffold.sh").exists(), case)
                self.assertEqual(yaml.safe_load((d / "case.yaml").read_text(encoding="utf-8"))["name"], case)
            self.assertTrue((d / "prompt.md").read_text(encoding="utf-8").strip(), case)
            names = set()
            for g in sorted((d / "graders").glob("*.md")):
                fm = self._grader_front_matter(g)
                self.assertIn(fm["type"], {"regex", "tool_order", "tool_used", "file_exists", "llm", "baseline"}, g.name)
                names.add(g.stem)
            self.assertGreaterEqual(len(names), 3, case)

    def test_no_grader_input_match_ends_with_dollar(self):
        for g in sorted((REPO / "evals").glob("*/graders/*.md")):
            fm = self._grader_front_matter(g)
            pattern = fm.get("input_match")
            if pattern is not None:
                self.assertFalse(str(pattern).endswith("$"), f"{g.parent.parent.name}/{g.name}")

    def test_every_case_has_skill_fired_grader(self):
        for prompt in sorted((REPO / "evals").glob("*/prompt.md")):
            d = prompt.parent
            sf = d / "graders/skill-fired.md"
            self.assertTrue(sf.is_file(), d.name)
            fm = self._grader_front_matter(sf)
            self.assertEqual(fm.get("type"), "tool_used", d.name)
            self.assertEqual(fm.get("tool"), "Skill", d.name)

    def test_edit_and_write_graders_have_twins(self):
        for prompt in sorted((REPO / "evals").glob("*/prompt.md")):
            d = prompt.parent
            edits = set()
            writes = set()
            for g in sorted((d / "graders").glob("*.md")):
                fm = self._grader_front_matter(g)
                if fm.get("type") != "tool_used" or fm.get("max") != 0:
                    continue  # only "must not write" checks need a twin; a required Edit has no Write twin
                sig = (fm.get("input_match"), fm.get("min"), fm.get("max"))
                if fm.get("tool") == "Edit":
                    edits.add(sig)
                elif fm.get("tool") == "Write":
                    writes.add(sig)
            if d.name == "ids-and-bulk-edits":
                continue  # Write is banned on purpose; the new task must be added with Edit
            self.assertEqual(edits, writes, d.name)

    def test_every_scaffold_builds_a_valid_acme(self):
        for scaffold in sorted((REPO / "evals").glob("*/scaffold.sh")):
            with self.subTest(scaffold.parent.name):
                self.check_scaffold(scaffold)

    def check_scaffold(self, scaffold):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        subprocess.run(["bash", str(scaffold)], cwd=tmp, check=True)
        if scaffold.parent.name == "status-report-from-acme":
            self.assertFalse((tmp / "pmo/documents/2026-03 - Status report.md").exists())
        if scaffold.parent.name == "no-pmo-no-setup":
            self.assertFalse((tmp / "pmo").exists())
            return
        p = subprocess.run([sys.executable, str(REPO / "skills/pmo-docs/scripts/render_views.py"), "--check"], cwd=tmp, capture_output=True)
        if scaffold.parent.name in ("renumber-batch-confirm", "renumber-no-references"):
            self.assertEqual(p.returncode, 1)
            self.assertIn("duplicate id T-5", p.stdout.decode("utf-8"))
            return
        if scaffold.parent.name in ("merge-conflict-markers", "merge-conflict-same-entry"):
            self.assertEqual(p.returncode, 1)
            self.assertIn("merge conflict markers", p.stdout.decode("utf-8"))
            return
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
