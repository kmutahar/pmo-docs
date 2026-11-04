"""Tests for scripts/pmo_common.py. Run from the repo root: python3 -m unittest discover tests"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


class Common(unittest.TestCase):
    def project(self, config=None, register=None):
        d = Path(tempfile.mkdtemp())
        (d / "pmo/registers").mkdir(parents=True)
        if config is not None:
            (d / "pmo/config.yaml").write_text(config, encoding="utf-8")
        if register:
            (d / "pmo/registers/tasks.yaml").write_text(register, encoding="utf-8")
        return d

    def test_default_config_is_consistent(self):
        c = pc.load_config(self.project())
        self.assertEqual(c["schema_version"], 1)
        for t in c["doc_types"].values():
            for g in t["generated_from"]:
                self.assertIn(g, c["registers"])
        for r in c["registers"].values():
            for v in r.get("enums", {}).values():
                self.assertIn(v, c["vocab"])

    def test_merge_rules(self):
        d = self.project("schema_version: 1\nproject: {name: Acme}\nvocab: {task_status: [a, b], rag: null}\n"
                         "doc_types: {roadmap: null}\n")
        c = pc.load_config(d)
        self.assertEqual(c["project"]["name"], "Acme")
        self.assertEqual(c["project"]["week_start"], "monday")  # map merged
        self.assertEqual(c["vocab"]["task_status"], ["a", "b"])  # list replaced
        self.assertNotIn("rag", c["vocab"])  # null removes
        self.assertNotIn("roadmap", c["doc_types"])

    def test_newer_schema_refused(self):
        with self.assertRaises(SystemExit):
            pc.load_config(self.project("schema_version: 99\n"))

    def test_missing_register_is_empty(self):
        d = self.project()
        c = pc.load_config(d)
        self.assertEqual(pc.load_register(d, c, "risks"), [])
        self.assertEqual(pc.load_register(d, c, "nope"), [])

    def test_register_and_override_lookup(self):
        d = self.project(register="tasks:\n  - {id: T-1, title: x, due: 2026-01-02}\n")
        c = pc.load_config(d)
        self.assertEqual(pc.load_register(d, c, "tasks")[0]["id"], "T-1")
        self.assertEqual(pc.find_asset(d, c, "templates", "roadmap.md")[1], "skill")
        (d / "pmo/templates").mkdir()
        (d / "pmo/templates/roadmap.md").write_text("x", encoding="utf-8")
        self.assertEqual(pc.find_asset(d, c, "templates", "roadmap.md")[1], "project")

    def test_front_matter_and_type(self):
        self.assertEqual(pc.doc_type("---\ntype: roadmap\n---\nbody"), "roadmap")
        self.assertIsNone(pc.doc_type("no front matter"))
        self.assertEqual(pc.split_front_matter("---\n: [\n---\nb")[0], {})

    def test_cell_escapes(self):
        self.assertEqual(pc.cell(["a|b", None, 3]), "a\\|b, , 3")
        self.assertEqual(pc.cell("x\ny"), "x y")
        self.assertEqual(pc.to_date("2026-01-02").day, 2)


if __name__ == "__main__":
    unittest.main()
