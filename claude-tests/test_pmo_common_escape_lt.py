# Tests that pmo_common.cell() and inline() write "<" as "&lt;". Run: python3 claude-tests/test_pmo_common_escape_lt.py
import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills/pmo-docs/scripts"))
import pmo_common as pc

class T(unittest.TestCase):
    def test_cell(self):
        self.assertEqual(pc.cell("<!-- x --> <b>hi</b>"), "&lt;!-- x --> &lt;b>hi&lt;/b>")
        self.assertEqual(pc.cell(["<a", {"k": "<v"}]), "&lt;a, k: &lt;v")
    def test_inline(self):
        self.assertEqual(pc.inline("a  <script>\nb"), "a &lt;script> b")
    def test_plain_unchanged(self):
        self.assertEqual(pc.cell("a|b"), r"a\|b")
        self.assertEqual(pc.inline("a  b"), "a b")

if __name__ == "__main__":
    unittest.main()
