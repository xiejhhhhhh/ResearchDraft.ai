from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validation.quality_gate import run_quality_gate


class QualityGateTests(unittest.TestCase):
    def test_quality_gate_passes_for_consistent_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft_dir = Path(tmp)
            (draft_dir / "draft.md").write_text(
                "# Test Draft\n\n"
                "## Abstract\nA short abstract.\n\n"
                "## Introduction\nA cited sentence (Smith, 2024).\n\n"
                "## Methods\nA method section.\n",
                encoding="utf-8",
            )
            (draft_dir / "draft.tex").write_text(
                "\\documentclass{article}\n"
                "\\usepackage[authoryear,round]{natbib}\n"
                "\\usepackage{xurl}\n"
                "\\usepackage[colorlinks=true]{hyperref}\n"
                "\\begin{document}\n"
                "\\begin{abstract}A short abstract.\\end{abstract}\n"
                "\\section{Introduction}\nA cited sentence \\citep{Smith2024Test}.\n"
                "\\section{Methods}\nA method section.\n"
                "\\bibliographystyle{plainnat}\n"
                "\\bibliography{draft}\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            (draft_dir / "draft.bib").write_text(
                "@article{Smith2024Test,\n"
                "  title = {A Test Paper},\n"
                "  author = {Smith, Jane},\n"
                "  year = {2024}\n"
                "}\n",
                encoding="utf-8",
            )
            (draft_dir / "draft.pdf").write_bytes(b"%PDF-1.4\n" + b"0" * 2048)
            report = run_quality_gate(
                draft_dir=draft_dir,
                file_paths={
                    "markdown": "draft.md",
                    "latex": "draft.tex",
                    "bibtex": "draft.bib",
                    "pdf": "draft.pdf",
                    "pdf_status": "PDF generated successfully using xelatex.exe.",
                },
                source_items=[{"title": "A Test Paper"}],
                submission_id="test",
            )
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["error_count"], 0)

    def test_quality_gate_fails_missing_bib_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft_dir = Path(tmp)
            (draft_dir / "draft.md").write_text("# Test Draft\n\n## Abstract\nA.\n", encoding="utf-8")
            (draft_dir / "draft.tex").write_text(
                "\\documentclass{article}\n"
                "\\usepackage[authoryear,round]{natbib}\n"
                "\\begin{document}\n"
                "\\begin{abstract}A.\\end{abstract}\n"
                "\\section{Introduction}\nMissing key \\citep{Missing2024}.\n"
                "\\bibliography{draft}\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            (draft_dir / "draft.bib").write_text("@article{Other2024,title={Other}}\n", encoding="utf-8")
            report = run_quality_gate(
                draft_dir=draft_dir,
                file_paths={"markdown": "draft.md", "latex": "draft.tex", "bibtex": "draft.bib"},
                source_items=[{"title": "Other"}],
                submission_id="test",
            )
            self.assertEqual(report["status"], "failed")
            self.assertGreaterEqual(report["error_count"], 1)


if __name__ == "__main__":
    unittest.main()

