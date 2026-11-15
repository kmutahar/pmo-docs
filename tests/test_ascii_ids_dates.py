"""Ids and dates hold ASCII digits only; a register date is not a datetime; split_front_matter leaves a BOM and CRLF to pc.read(). Run from the repo root: python3 -m unittest tests.test_ascii_ids_dates"""
import datetime
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import generate  # noqa: E402
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402

ARABIC_DATE = "٢٠٢٦-٠٣-٠١"  # 2026-03-01 in Arabic-Indic digits
ARABIC_ID = "T-١٢"                                          # T-12


class AsciiOnly(unittest.TestCase):
    def test_to_date(self):
        self.assertEqual(pc.to_date("2026-03-01"), datetime.date(2026, 3, 1))
        self.assertEqual(pc.to_date(datetime.date(2026, 3, 1)), datetime.date(2026, 3, 1))
        self.assertEqual(pc.to_date(datetime.datetime(2026, 3, 1, 9, 30)), datetime.date(2026, 3, 1))  # tolerant: front matter stamps
        with self.assertRaises(ValueError):
            pc.to_date(ARABIC_DATE)

    def test_real_date(self):
        self.assertTrue(render_views.real_date("2026-03-01"))
        self.assertTrue(render_views.real_date(datetime.date(2026, 3, 1)))
        self.assertFalse(render_views.real_date(ARABIC_DATE))
        self.assertFalse(render_views.real_date(datetime.datetime(2026, 3, 1, 9, 30)))

    def test_id_numbers_ignore_other_digits(self):
        self.assertEqual(pc.id_num("T-12"), 12)
        self.assertEqual(pc.id_num(ARABIC_ID), 0)
        self.assertEqual(generate.id_number("T-12"), 12)
        self.assertEqual(generate.id_number(ARABIC_ID), 0)


class FrontMatterInput(unittest.TestCase):
    RAW = "\ufeff---\r\ntitle: x\r\n---\r\nbody\r\n"

    def test_raw_string_is_not_normalised(self):
        self.assertEqual(pc.split_front_matter(self.RAW), (None, self.RAW))  # the caller reads with pc.read()

    def test_pc_read_normalises(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.md"
            f.write_bytes(self.RAW.encode("utf-8"))
            self.assertEqual(pc.split_front_matter(pc.read(f)), ({"title": "x"}, "body\n"))


if __name__ == "__main__":
    unittest.main()
