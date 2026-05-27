from __future__ import annotations

import unittest

from export.bibtex import citation_key, generate_bibtex
from export.latex_text import replace_plain_urls_with_latex, safe_latex


class ExportHelperTests(unittest.TestCase):
    def test_citation_key_is_stable_and_bibtex_is_generated(self) -> None:
        item = {
            "title": "Transformer Models for Long-Term AGN Prediction",
            "authors": ["Jane Smith"],
            "year": "2024",
            "publication": "Journal of Testing",
        }
        self.assertEqual(citation_key(item, 0), "Smith2024Transformer1")
        bibtex = generate_bibtex([item])
        self.assertIn("@article{Smith2024Transformer1", bibtex)
        self.assertIn("journal = {Journal of Testing}", bibtex)

    def test_latex_url_and_text_escaping(self) -> None:
        text = "Data: https://example.org/data - products/file_name?a=1&b=2"
        converted = replace_plain_urls_with_latex(text)
        self.assertIn("\\href{https://example.org/data-products/file_name?a=1&b=2}", converted)
        self.assertIn("\\nolinkurl{https://example.org/data-products/file_name?a=1&b=2}", converted)
        self.assertEqual(safe_latex("A_B & 50%"), "A\\_B \\& 50\\%")


if __name__ == "__main__":
    unittest.main()

