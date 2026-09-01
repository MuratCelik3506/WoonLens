from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from woonlens.application.ports.reports import PdfReportRenderer
from woonlens.application.services.reporting import ComparisonEvidenceReportService
from woonlens.domain.reporting import ComparisonEvidenceReport
from woonlens.entrypoints.api.addresses import SourceResponse
from woonlens.entrypoints.api.comparisons import (
    LiveComparisonRequest,
    LiveHomeComparisonResponse,
)

router = APIRouter(prefix="/comparison-downloads", tags=["comparison downloads"])


class ComparisonEvidenceReportResponse(BaseModel):
    schema_version: str
    generated_at: datetime
    rules_version: str
    comparison: LiveHomeComparisonResponse
    sources: list[SourceResponse]
    warnings: list[str]
    limitations: list[str]

    @classmethod
    def from_domain(
        cls, report: ComparisonEvidenceReport
    ) -> "ComparisonEvidenceReportResponse":
        comparison = LiveHomeComparisonResponse.from_domain(report.comparison)
        return cls(
            schema_version=report.schema_version,
            generated_at=report.generated_at,
            rules_version=report.comparison.rules_version,
            comparison=comparison,
            sources=[SourceResponse.from_domain(source) for source in report.sources],
            warnings=[notice.message for notice in report.comparison.notices],
            limitations=list(report.limitations),
        )


def get_report_service(request: Request) -> ComparisonEvidenceReportService:
    return cast(ComparisonEvidenceReportService, request.app.state.report_service)


def get_pdf_renderer(request: Request) -> PdfReportRenderer:
    return cast(PdfReportRenderer, request.app.state.pdf_report_renderer)


@router.post("/json", response_model=ComparisonEvidenceReportResponse)
async def download_json_report(
    request: Request,
    payload: LiveComparisonRequest,
) -> Response:
    report = await get_report_service(request).generate(tuple(payload.address_ids))
    response = ComparisonEvidenceReportResponse.from_domain(report)
    timestamp = report.generated_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Response(
        content=response.model_dump_json(indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="woonlens-comparison-{timestamp}.json"'
            ),
            "Cache-Control": "no-store",
        },
    )


@router.post("/pdf")
async def download_pdf_report(
    request: Request,
    payload: LiveComparisonRequest,
) -> Response:
    report = await get_report_service(request).generate(tuple(payload.address_ids))
    content = get_pdf_renderer(request).render(report)
    timestamp = report.generated_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="woonlens-comparison-{timestamp}.pdf"'
            ),
            "Cache-Control": "no-store",
        },
    )
