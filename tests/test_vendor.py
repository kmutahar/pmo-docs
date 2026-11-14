"""Tests for the vendored and pruned PyYAML. Run from the repo root: python3 -m unittest discover tests"""
import datetime
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # importing the shipped scripts must leave no __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # child scripts must leave no __pycache__ either


class VendoredYaml(unittest.TestCase):
    def test_safe_load_and_dump_work(self):
        data = {"id": "T-1", "title": "Test task", "due": datetime.date(2026, 3, 10)}
        text = pc.yaml.safe_dump(data, default_flow_style=True)
        loaded = pc.yaml.safe_load(text)
        self.assertEqual(loaded["id"], "T-1")
        self.assertEqual(loaded["title"], "Test task")
        self.assertEqual(loaded["due"], datetime.date(2026, 3, 10))

    def test_unsafe_api_is_gone(self):
        yaml = pc.yaml
        for name in ("load", "full_load", "unsafe_load", "load_all", "FullLoader", "UnsafeLoader", "Loader"):
            self.assertFalse(hasattr(yaml, name), f"yaml.{name} should not exist")
        for name in ("FullConstructor", "UnsafeConstructor", "Constructor"):
            self.assertFalse(hasattr(yaml.constructor, name), f"yaml.constructor.{name} should not exist")

    def test_python_tags_are_refused(self):
        with self.assertRaises(pc.yaml.constructor.ConstructorError):
            pc.yaml.safe_load("!!python/object/apply:os.system ['true']")

    def test_vendored_copy_is_the_one_loaded(self):
        repo_root = Path(__file__).resolve().parents[1]
        vendor_dir = (repo_root / "skills/pmo-docs/scripts/_vendor/yaml").resolve()
        loaded_file = Path(pc.yaml.__file__).resolve()
        self.assertTrue(str(loaded_file).startswith(str(vendor_dir)), f"{loaded_file} not in {vendor_dir}")

        scripts_dir = str(repo_root / "skills/pmo-docs/scripts")
        cmd = [sys.executable, "-c", f"import sys; sys.path.insert(0, {scripts_dir!r}); import pmo_common as pc; print(pc.yaml.__file__)"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        sub_file = Path(res.stdout.strip()).resolve()
        self.assertTrue(str(sub_file).startswith(str(vendor_dir)), f"{sub_file} not in {vendor_dir}")

    def test_cyaml_does_not_exist(self):
        repo_root = Path(__file__).resolve().parents[1]
        cyaml = repo_root / "skills/pmo-docs/scripts/_vendor/yaml/cyaml.py"
        self.assertFalse(cyaml.exists(), "cyaml.py should not exist in vendored PyYAML")

    def test_default_registrations_cannot_widen_safe_load(self):
        # upstream never touched SafeLoader from a default registration; keep it so
        yaml = pc.yaml
        calls = [(yaml.add_constructor, ("!x", lambda l, n: 1)),
                 (yaml.add_multi_constructor, ("!x", lambda l, s, n: 1)),
                 (yaml.add_implicit_resolver, ("!x", __import__("re").compile("zzz"))),
                 (yaml.add_path_resolver, ("!x", ["a"]))]
        for fn, args in calls:
            with self.assertRaises(TypeError, msg=fn.__name__):
                fn(*args)
        self.assertEqual(yaml.YAMLObject.yaml_loader, [])
        self.assertNotIn("!x", yaml.SafeLoader.yaml_constructors)

    def test_version_file_matches_vendored_yaml(self):
        version_file = Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts/_vendor/VERSION"
        first_line = version_file.read_text(encoding="utf-8").splitlines()[0]
        m = re.match(r"^PyYAML\s+(\S+)", first_line)
        self.assertIsNotNone(m, first_line)
        self.assertEqual(m.group(1), pc.yaml.__version__)

if __name__ == "__main__":
    unittest.main()
