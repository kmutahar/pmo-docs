"""Budget currency and project exchange rates (render_views.py) on a temp copy of examples/acme. Run from the repo root: python3 -m unittest tests.test_budget_currency"""
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True  # importing the shipped scripts must leave no __pycache__
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import render_views as rv  # noqa: E402


class BudgetCurrency(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def edit(self, path, old, new):
        f = self.root / path
        text = f.read_text(encoding="utf-8")
        self.assertIn(old, text)
        f.write_text(text.replace(old, new), encoding="utf-8")

    def run_rv(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = rv.main(["--project", str(self.root), *extra])
        return code, out.getvalue()

    def test_acme_renders_clean_and_shows_the_column(self):
        self.assertEqual(self.run_rv("--check")[0], 0)
        view = (self.root / "pmo/views/budget.md").read_text(encoding="utf-8")
        self.assertIn("| currency |", view)
        self.assertIn("| EUR |", view)

    def test_missing_rate_says_what_to_add(self):
        self.edit("pmo/config.yaml", "  exchange_rates: { EUR: 1.08 }\n", "")
        code, out = self.run_rv()
        self.assertEqual(code, 1)
        self.assertIn("budget B-003: currency EUR has no rate. Add project.exchange_rates.EUR "
                      "(project currency units per 1 EUR) to pmo/config.yaml", out)

    def test_row_currency_without_project_currency(self):
        self.edit("pmo/config.yaml", "  currency: USD\n", "")
        code, out = self.run_rv()
        self.assertEqual(code, 1)
        self.assertIn("budget B-003: currency EUR needs a project currency. Set project.currency", out)

    def test_row_with_no_currency_never_errors_without_project_currency(self):
        self.edit("pmo/config.yaml", "  currency: USD\n  exchange_rates: { EUR: 1.08 }\n", "")
        self.edit("pmo/registers/budget.yaml", "currency: EUR, ", "")
        self.assertEqual(self.run_rv()[0], 0)

    def test_bad_codes(self):
        self.edit("pmo/config.yaml", "currency: USD", "currency: usd")
        self.edit("pmo/config.yaml", "{ EUR: 1.08 }", "{ eur: 1.08 }")
        code, out = self.run_rv()
        self.assertEqual(code, 2)
        self.assertIn("project.currency `usd` must be 3 uppercase letters", out)
        self.assertIn("project.exchange_rates key `eur` must be 3 uppercase letters", out)

    def test_bad_rates(self):
        for rate in ("0", "-1", "abc", "true"):
            with self.subTest(rate=rate):
                self.edit("pmo/config.yaml", "EUR: 1.08", f"EUR: {rate}")
                code, out = self.run_rv()
                self.assertEqual(code, 2)
                self.assertIn("project.exchange_rates.EUR", out)
                self.assertIn("must be a positive number", out)
                self.edit("pmo/config.yaml", f"EUR: {rate}", "EUR: 1.08")

    def test_rate_for_the_project_currency(self):
        self.edit("pmo/config.yaml", "{ EUR: 1.08 }", "{ EUR: 1.08, USD: 1 }")
        code, out = self.run_rv()
        self.assertEqual(code, 2)
        self.assertIn("project.exchange_rates.USD is not needed", out)

    def test_bad_row_currency(self):
        self.edit("pmo/registers/budget.yaml", "currency: EUR", "currency: euro")
        code, out = self.run_rv()
        self.assertEqual(code, 1)
        self.assertIn("budget B-003: currency 'euro' must be 3 uppercase letters", out)


if __name__ == "__main__":
    unittest.main()
