from __future__ import annotations

from models import ResearchIdeaRequest


def dataset_access_hints(request: ResearchIdeaRequest) -> str:
    """Return conservative public URL hints for named datasets/platforms."""
    text = " ".join([request.idea or "", request.field or "", request.data_description or ""]).lower()
    hints = []
    mappings = [
        (["lsst", "rubin"], "Rubin/LSST data access: https://rubinobservatory.org/for-scientists/data-products/data-access"),
        (["lamost"], "LAMOST data releases: https://www.lamost.org/lmusers/ and https://www.lamost.org/dr12"),
        (["einstein probe", " ep ", "ep satellite"], "Einstein Probe mission information: https://www.esa.int/Science_Exploration/Space_Science/Einstein_Probe_factsheet"),
        (["plantvillage"], "PlantVillage: https://plantvillage.psu.edu/"),
        (["kaggle", "plantdisease"], "Kaggle Plant Disease dataset: https://www.kaggle.com/datasets/emmarex/plantdisease"),
        (["soilgrids", "isric"], "ISRIC SoilGrids: https://soilgrids.org/"),
        (["era5"], "ERA5/Copernicus Climate Data Store: https://cds.climate.copernicus.eu/"),
        (["sentinel-2", "sentinel 2"], "Sentinel-2 dataset catalog: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2"),
        (["radiant mlhub", "radiant machine learning hub"], "Radiant MLHub: https://mlhub.earth/"),
    ]
    padded = f" {text} "
    for keywords, hint in mappings:
        if any(keyword in padded for keyword in keywords):
            hints.append(hint)
    if not hints:
        return "No dataset access URLs were confidently recognized from the user input. Do not invent URLs; state that access links should be verified manually when necessary."
    return "\n".join(f"- {hint}" for hint in dict.fromkeys(hints))


def build_publishable_outline_prompt(request: ResearchIdeaRequest, literature_context: str) -> str:
    """Build the strict manuscript-outline prompt used by all model providers."""
    data_description = request.data_description or (
        "No explicit data description was provided. Infer only conservative data needs "
        "from the research topic and the cited literature, and label inferred parts clearly."
    )
    target_journal = request.journal or "General Academic Journal"
    return f"""You are writing an English, publishable-paper-oriented research draft outline. The output must be detailed enough to guide later manuscript writing, not a short abstract-style proposal.

Research Topic:
{request.idea}

Research Field / Aim:
{request.field}

Data Description:
{data_description}

Target Journal:
{target_journal}

Recognized dataset access hints:
{dataset_access_hints(request)}

{literature_context}

Mandatory workflow before writing:
- First synthesize every provided reference. For each cited paper, extract its research question, data, methods, scientifically meaningful findings, limitations, and relevance to this study.
- Use citation weights to decide which papers deserve more attention, but do not cite any paper that is not listed in the provided literature context.
- If supplemental external references are included, distinguish them from existing Zotero references in the writing and references list.
- Write in natural academic English. Avoid AI-like transitions, arbitrary bullet lists inside prose sections, and unsupported claims.

Required output structure:

# Title
Provide a specific, journal-style title.

# Abstract
Write 300-500 words summarizing background, data, method, expected contribution, and significance.

# Literature Synthesis Before Writing
Write one compact paragraph for each important reference. Each paragraph must summarize the paper's abstract/core outline, data, methods, major scientific findings, limitations, and how strongly it should inform this draft. Use author-year citations in the paragraph text.

# Introduction
Write 4-5 balanced paragraphs in this exact logical order. Paragraph 1 introduces the broad research background and key concepts. Paragraph 2 reviews current research status using the provided literature. Paragraph 3 identifies current gaps, and the gaps must connect directly to this study's innovation and purpose. Paragraph 4 states what this study does and why it matters. If a paragraph becomes too long, split it naturally into paragraph 5. Use author-year citations in Markdown output.

# Data
Write 3 paragraphs. Paragraph 1 introduces all data sources and their roles by merging the user-provided Data Description with the data patterns extracted from the provided references. Paragraphs 2 and 3 explain data construction and preprocessing, including alignment, normalization, denoising, label construction, quality control, and uncertainty issues only when they are relevant to the stated idea and data. Do not force equations into the Data section. Do not mention vegetation indices, NDVI, crop formulas, or remote-sensing formulas unless the user's data description or the provided references explicitly require them. If public datasets, surveys, missions, or platforms are named, include official or project URLs when they are known from the input or literature metadata; otherwise state conservatively that the access URL should be verified manually. If no paper-specific GitHub project is available, describe that a demo_data.py workflow should be generated and used as the implementation basis.

# Methods
Write 3-4 paragraphs. Explain the proposed model construction, model analysis, and data-analysis workflow. Use TeX-style mathematical notation only for equations that are directly relevant to the proposed method, such as multimodal feature fusion, transformer attention, forecasting losses, uncertainty estimation, or validation metrics. Put every displayed equation on its own paragraph using either $$...$$ or \\[...\\]. Do not split inline math across line breaks. If no GitHub paper project is available, describe a demo_method.py workflow and write the methods as if the model implementation will be checked against that script.

# Results
Write 3-4 paragraphs with no literature citations. Each paragraph should describe one expected result or conclusion that answers the research gaps identified in the Introduction and highlights the innovation of the new method. Do not put the figure/table list inside this section.

# Figure and Table Plan
Create a standalone figure/table plan after Results. Do not use tables in this section. Write 5-7 short paragraphs in the order of the manuscript narrative. Each paragraph must name the figure or table directly, for example "Fig. 1: AI-ready disease-monitoring data pipeline" or "Table 1: Baseline comparison and innovation-specific ablation". The plan must combine figures and tables into one continuous logical storyline: data pipeline, model architecture, comparison against existing baselines, innovation-specific validation, uncertainty or robustness, field-scale application, and decision-support output when relevant. Each paragraph should explain which current research limitation the figure/table addresses and how it highlights this study's innovation.

# Discussion
Write 4-5 paragraphs. The first 2-3 paragraphs expand on what the expected results would mean. The fourth paragraph compares the study with existing literature using author-year citations. The fifth paragraph states the study's significance, limitations, and future work. Keep the discussion connected to the Introduction gaps.

# References
List only the references provided in the literature context. Use clean academic reference formatting. Do not invent authors, journals, DOIs, or years.
"""

