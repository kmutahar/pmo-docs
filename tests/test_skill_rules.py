"""Tests for SKILL.md and playbook rules. Run from the repo root: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


class SkillRules(unittest.TestCase):
    def _skill(self):
        text = (pc.SKILL / "SKILL.md").read_text(encoding="utf-8")
        fm, _ = pc.split_front_matter(text, strict=True)
        return fm, text

    def _playbook(self, name):
        return (pc.SKILL / "references" / name).read_text(encoding="utf-8")

    def test_description_fits_and_names_the_trigger(self):
        fm, _ = self._skill()
        desc = fm["description"]
        self.assertLessEqual(len(desc), 1024)
        self.assertIn("Use only in a project that has a `pmo/` folder", desc)

    def test_step_1_handles_a_missing_project_office(self):
        _, text = self._skill()
        self.assertIn("ask once whether to set one up", text)
        self.assertIn("git rev-parse --show-toplevel", text)

    def test_routing_has_a_question_row(self):
        _, text = self._skill()
        self.assertIn("a question about the project's facts", text)

