from typing import Protocol

from woonlens.domain.reporting import ComparisonEvidenceReport


class PdfReportRenderer(Protocol):
    def render(self, report: ComparisonEvidenceReport) -> bytes: ...
