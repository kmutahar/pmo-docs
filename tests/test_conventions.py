"""Every key in config.default.yaml is named in backticks in references/conventions.md. Run from the repo root: python3 -m unittest tests.test_conventions"""
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/pmo-docs"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SKILL / "scripts"))
import pmo_common as pc  # noqa: E402

# The per-item block under these maps is written once as a pattern, not once per item.
PATTERNS = {"registers": "<name>", "doc_types": "<type>", "languages": "<code>"}
# languages.draft and languages.translations are keys, not codes.
PLAIN = {"languages": {"draft", "translations"}}


def key_paths(node, prefix=()):
    """Yield the dotted path of every key that has no sub-keys to check; lists are leaves.
    The keys under `enums` and `refs` are field names, not config keys, so those two are leaves."""
    for key, value in node.items():
        if len(prefix) == 1 and prefix[0] in PATTERNS and key not in PLAIN.get(prefix[0], ()):
            key = PATTERNS[prefix[0]]
        path = prefix + (str(key),)
        if isinstance(value, dict) and value and path[-1] not in ("enums", "refs"):
            yield from key_paths(value, path)
        elif not (len(path) == 2 and path[1] in PATTERNS.values()):
            yield ".".join(path)


def documented(path, text):
    """Documented = the full path is in backticks (`registers.tasks.blocked` covers registers.<name>.blocked), or,
    under languages.<code> and vocab, the bare key (`dir`, `task_status`)."""
    ticks = set()
    for t in re.findall(r"`([^`:]+)", text):
        ticks.add(re.sub(r"^(registers|doc_types|languages)\.[^.]+\.", lambda m: f"{m[1]}.{PATTERNS[m[1]]}.", t))
        ticks.add(t)
    return path in ticks or (path.startswith(("languages.<code>.", "vocab.")) and path.rsplit(".", 1)[-1] in ticks)


class ConfigIsDocumented(unittest.TestCase):
    def test_every_default_key_is_in_conventions(self):
        cfg = pc.yaml.safe_load(pc.read(SKILL / "assets/config.default.yaml"))
        text = (SKILL / "references/conventions.md").read_text(encoding="utf-8")
        paths = sorted(set(key_paths(cfg)))
        self.assertGreater(len(paths), 50)  # the walk found the file
        missing = [p for p in paths if not documented(p, text)]
        self.maxDiff = None
        self.assertEqual(missing, [], "keys missing from references/conventions.md")


if __name__ == "__main__":
    unittest.main()
