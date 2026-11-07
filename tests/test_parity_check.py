"""Tests for scripts/parity_check.py on a copy of examples/acme. Run from the repo root: python3 -m unittest discover tests"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_fixture as tf  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "skills/pmo-docs/scripts/parity_check.py"
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import parity_check as pc_tool  # noqa: E402
import pmo_common as pc  # noqa: E402


def run(project, *args):
    cmd = [sys.executable, str(TOOL), "--project", str(project)] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


class ParityCheck(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(REPO / "examples/acme", self.root / "acme")
        self.proj = self.root / "acme"
        self.docs = self.proj / "pmo/documents"
        self.dec_log = self.docs / "Decision log.md"
        self.orig_text = self.dec_log.read_text(encoding="utf-8")
        self.addCleanup(shutil.rmtree, self.root)

    def test_help(self):
        code, out = run(self.proj, "--help")
        self.assertEqual(code, 0)
        self.assertIn("usage", out.lower())

    def test_matching_translation_is_ok(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        trans_file = self.docs / "Decision log.xx.md"
        trans_file.write_text(trans_text, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 0, out)
        self.assertIn("ok    pmo/documents/Decision log.xx.md", out)
        self.assertIn("0 file(s) differ from their originals", out)

    def test_no_translations_exits_0(self):
        code, out = run(self.proj)
        self.assertEqual(code, 0, out)
        self.assertIn("0 file(s) differ from their originals", out)

    def test_row_removed_is_reported(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        # remove one Summary table row
        lines = trans_text.splitlines()
        filtered = [ln for ln in lines if "DEC-2 |" not in ln]
        (self.docs / "Decision log.xx.md").write_text("\n".join(filtered) + "\n", encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("Summary", out)
        self.assertIn("rows", out)

    def test_column_removed(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        # remove Date column from Summary table
        lines = trans_text.splitlines()
        modified = []
        for ln in lines:
            if ln.startswith("|") and ("Datox" in ln or "2026-03-09" in ln or "2026-02-12" in ln or "---|" in ln):
                cells = [c.strip() for c in ln.split("|")[1:-1]]
                del cells[3]  # delete Date cell
                modified.append("| " + " | ".join(cells) + " |")
            else:
                modified.append(ln)
        (self.docs / "Decision log.xx.md").write_text("\n".join(modified) + "\n", encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("Summary", out)
        self.assertIn("column count differs", out)

    def test_heading_level_changed(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        modified = trans_text.replace("### DEC-2", "#### DEC-2")
        (self.docs / "Decision log.xx.md").write_text(modified, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("heading level", out)

    def test_heading_removed(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        modified = trans_text.replace("## Questiones apertas\n- Nulla ancora.\n", "")
        (self.docs / "Decision log.xx.md").write_text(modified, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("heading count differs", out)
        self.assertNotIn("table 1", out)

    def test_changed_number_is_reported(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        # change date in DEC-2 bullet from 2026-03-09 to 2026-03-10
        modified = trans_text.replace("2026-03-09 - **Decidat per:** sam", "2026-03-10 - **Decidat per:** sam")
        (self.docs / "Decision log.xx.md").write_text(modified, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("Host on shared cloud", out)
        self.assertIn("numbers differ", out)

    def test_changed_id_is_reported(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        modified = trans_text.replace("DEC-1", "DEC-7")
        (self.docs / "Decision log.xx.md").write_text(modified, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("ids differ", out)

    def test_digits_from_config(self):
        tf.enable_languages(self.proj, ("xx",), block='    digits: "٠١٢٣٤٥٦٧٨٩"\n')
        trans_text = tf.make_translation(self.orig_text)
        # write the dates of the Summary table in those digits
        modified = trans_text.replace("2026-03-09", "٢٠٢٦-٠٣-٠٩").replace("2026-02-12", "٢٠٢٦-٠٢-١٢")
        trans_file = self.docs / "Decision log.xx.md"
        trans_file.write_text(modified, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 0, out)

        # same text without digits config exits 1
        cfg_file = self.proj / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8").replace('    digits: "٠١٢٣٤٥٦٧٨٩"\n', ""), encoding="utf-8")
        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("numbers differ", out)

    def test_connectors_from_config(self):
        tf.enable_languages(self.proj, ("xx",), block="    connectors:\n      of: med\n")
        # Add a cell '3 of 5' to both documents
        orig_with_cell = self.orig_text.replace(
            "| DEC-2 | Use the shared cloud account |",
            "| DEC-2 | Use the shared cloud account (3 of 5) |"
        )
        self.dec_log.write_text(orig_with_cell, encoding="utf-8")

        trans_text = tf.make_translation(orig_with_cell)
        trans_with_cell = trans_text.replace("3 of 5", "3 med 5")
        (self.docs / "Decision log.xx.md").write_text(trans_with_cell, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 0, out)

        # without the config line, exit 1
        cfg_file = self.proj / "pmo/config.yaml"
        cfg_file.write_text(cfg_file.read_text(encoding="utf-8").replace("    connectors:\n      of: med\n", ""), encoding="utf-8")
        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("numbers differ", out)

    def test_ids_next_to_other_script(self):
        tf.enable_languages(self.proj, ("xx",))
        # glued to a non-Latin letter: \u0633 is Arabic letter seen
        orig = self.orig_text + "\n\n\u0633DEC-1 note.\n"
        self.dec_log.write_text(orig, encoding="utf-8")

        trans = tf.make_translation(orig)
        (self.docs / "Decision log.xx.md").write_text(trans, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 0, out)

    def test_original_missing_exits_1(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text).replace("translation_of: Decision log.md", "translation_of: Missing.md")
        (self.docs / "Decision log.xx.md").write_text(trans_text, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("missing", out)

    def test_lang_not_in_config_exits_1(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text).replace("lang: xx", "lang: yy")
        (self.docs / "Decision log.yy.md").write_text(trans_text, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 1, out)
        self.assertIn("lang `yy` not in config", out)

    def test_file_without_translation_of_exits_1(self):
        code, out = run(self.proj, str(self.dec_log))
        self.assertEqual(code, 1, out)
        self.assertIn("no translation_of", out)

    def test_sign_counts_but_range_and_hyphenated_word_do_not(self):
        no_ids = re.compile(r"(?!)")
        n = lambda t: pc_tool.numbers(t, {}, no_ids)
        self.assertNotEqual(n("down -5%"), n("down +5%"))
        self.assertEqual(n("pages 3-5, COVID-19"), ["3~5", "19"])

    def test_prose_wording_is_not_compared(self):
        tf.enable_languages(self.proj, ("xx",))
        trans_text = tf.make_translation(self.orig_text)
        # Change words of a sentence with no IDs or numbers
        modified = trans_text.replace("Besoing hospitatione barata", "Totam nova phrasis sine numeris")
        (self.docs / "Decision log.xx.md").write_text(modified, encoding="utf-8")

        code, out = run(self.proj)
        self.assertEqual(code, 0, out)


    def test_digits_that_reuse_ascii_digits_map_in_one_pass(self):
        info = {"digits": "1023456789"}
        self.assertEqual(pc_tool.normalise("0 1 2", info), "1 0 2")

    def test_bad_language_config_exits_2(self):
        tf.enable_languages(self.proj, ("xx",), block="  yy: nonsense\n")
        cfg = self.proj / "pmo/config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8").replace("draft: en", "draft: qq"), encoding="utf-8")
        code, out = run(self.proj)
        self.assertEqual(code, 2, out)
        self.assertIn("languages.qq", out)


if __name__ == "__main__":
    unittest.main()
