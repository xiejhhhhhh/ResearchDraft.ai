from __future__ import annotations

import unittest

from generation.prompts import build_publishable_outline_prompt
from literature.external_search import build_external_search_query, clean_literature_items
from literature.ranking import parse_easyscholar_rank, weight_literature_items
from models import ResearchIdeaRequest


class LiteratureAndPromptTests(unittest.TestCase):
    def test_external_query_specializes_agn_topic(self) -> None:
        request = ResearchIdeaRequest(
            idea="Long-term AGN outburst prediction",
            field="machine learning astronomy computing",
            journal=None,
            output_format="tex",
            add_to_zotero=False,
            email="test@example.com",
            data_description="LSST LAMOST Einstein Probe FITS light curves spectra images",
            literature_mode="external",
        )
        query = build_external_search_query(request, [])
        self.assertIn("active galactic nuclei", query)
        self.assertIn("machine learning", query)

    def test_clean_literature_items_adds_safe_abstract(self) -> None:
        items = [{"title": "A Metadata Only Paper", "publication": "Test Journal", "year": "2024"}]
        cleaned = clean_literature_items(items, query="test query")
        self.assertEqual(len(cleaned), 1)
        self.assertIn("No abstract was returned", cleaned[0]["abstract"])

    def test_easyscholar_rank_parser_and_weighting(self) -> None:
        payload = {
            "data": {
                "officialRank": {"all": {"sci": "Q1"}},
                "customRank": {"rankInfo": [], "rank": []},
            }
        }
        parsed = parse_easyscholar_rank(payload)
        self.assertEqual(parsed["journal_score"], 1.0)

        weighted = weight_literature_items([
            {
                "title": "Transformer models for AGN outburst prediction",
                "abstract": "machine learning astronomy time-domain variability",
                "citation_count": 20,
                "influential_citation_count": 2,
                "publication": "",
            }
        ], idea="AGN outburst prediction using transformer machine learning")
        self.assertEqual(len(weighted), 1)
        self.assertGreater(weighted[0]["citation_weight"], 0)

    def test_prompt_contains_required_sections(self) -> None:
        request = ResearchIdeaRequest(
            idea="Early Detection of Potato Diseases During the Growing Season Using Multi-Agent Machine Learning",
            field="precision agriculture",
            journal="Computers and Electronics in Agriculture",
            output_format="tex",
            add_to_zotero=False,
            email="test@example.com",
            data_description="Sentinel-2, ERA5, SoilGrids, UAV imagery, PlantVillage",
        )
        prompt = build_publishable_outline_prompt(request, "Literature context here.")
        self.assertIn("# Introduction", prompt)
        self.assertIn("# Data", prompt)
        self.assertIn("# Methods", prompt)
        self.assertIn("# Figure and Table Plan", prompt)
        self.assertIn("Sentinel-2 dataset catalog", prompt)


if __name__ == "__main__":
    unittest.main()

