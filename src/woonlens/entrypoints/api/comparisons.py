from typing import Self, cast
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, model_validator

from woonlens.application.services.comparison import LiveHomeComparisonService
from woonlens.domain.comparison import (
    ComparedHome,
    ComparedValue,
    ComparisonInsight,
    ComparisonNotice,
    LiveHomeComparison,
    MetricComparison,
    MetricDefinition,
    MetricScalar,
    SourceAudit,
)
from woonlens.entrypoints.api.addresses import HomeOverviewResponse

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


class LiveComparisonRequest(BaseModel):
    address_ids: list[UUID] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def addresses_are_unique(self) -> Self:
        if len(self.address_ids) != len(set(self.address_ids)):
            raise ValueError("address_ids must be unique")
        return self


class ComparedHomeResponse(BaseModel):
    address_id: UUID
    overview: HomeOverviewResponse | None
    unavailable_reason: str | None

    @classmethod
    def from_domain(cls, home: ComparedHome) -> Self:
        return cls(
            address_id=home.address_id,
            overview=(
                HomeOverviewResponse.from_domain(home.overview)
                if home.overview is not None
                else None
            ),
            unavailable_reason=home.unavailable_reason,
        )


class MetricDefinitionResponse(BaseModel):
    key: str
    label: str
    scope: str
    unit: str
    definition: str
    supports_delta: bool

    @classmethod
    def from_domain(cls, metric: MetricDefinition) -> Self:
        return cls(
            key=metric.key,
            label=metric.label,
            scope=metric.scope,
            unit=metric.unit,
            definition=metric.definition,
            supports_delta=metric.supports_delta,
        )


class ComparedValueResponse(BaseModel):
    address_id: UUID
    value: MetricScalar | None
    delta_from_baseline: float | int | None
    missing_reason: str | None
    is_baseline: bool

    @classmethod
    def from_domain(cls, value: ComparedValue) -> Self:
        return cls(
            address_id=value.address_id,
            value=value.value,
            delta_from_baseline=value.delta_from_baseline,
            missing_reason=value.missing_reason,
            is_baseline=value.is_baseline,
        )


class MetricComparisonResponse(BaseModel):
    metric: MetricDefinitionResponse
    values: list[ComparedValueResponse]

    @classmethod
    def from_domain(cls, comparison: MetricComparison) -> Self:
        return cls(
            metric=MetricDefinitionResponse.from_domain(comparison.metric),
            values=[
                ComparedValueResponse.from_domain(value) for value in comparison.values
            ],
        )


class ComparisonNoticeResponse(BaseModel):
    code: str
    message: str

    @classmethod
    def from_domain(cls, notice: ComparisonNotice) -> Self:
        return cls(code=notice.code, message=notice.message)


class ComparisonInsightResponse(BaseModel):
    rule_id: str
    metric_key: str
    classification: str
    address_ids: list[UUID]
    message: str

    @classmethod
    def from_domain(cls, insight: ComparisonInsight) -> Self:
        return cls(
            rule_id=insight.rule_id,
            metric_key=insight.metric_key,
            classification=insight.classification,
            address_ids=list(insight.address_ids),
            message=insight.message,
        )


class SourceAuditResponse(BaseModel):
    rule_id: str
    address_id: UUID
    classification: str
    fields: tuple[str, str]
    values: tuple[MetricScalar | None, MetricScalar | None]
    message: str

    @classmethod
    def from_domain(cls, audit: SourceAudit) -> Self:
        return cls(
            rule_id=audit.rule_id,
            address_id=audit.address_id,
            classification=audit.classification,
            fields=audit.fields,
            values=audit.values,
            message=audit.message,
        )


class LiveHomeComparisonResponse(BaseModel):
    homes: list[ComparedHomeResponse]
    metrics: list[MetricComparisonResponse]
    notices: list[ComparisonNoticeResponse]
    rules_version: str
    insights: list[ComparisonInsightResponse]
    audits: list[SourceAuditResponse]

    @classmethod
    def from_domain(cls, comparison: LiveHomeComparison) -> Self:
        return cls(
            homes=[ComparedHomeResponse.from_domain(home) for home in comparison.homes],
            metrics=[
                MetricComparisonResponse.from_domain(metric)
                for metric in comparison.metrics
            ],
            notices=[
                ComparisonNoticeResponse.from_domain(notice)
                for notice in comparison.notices
            ],
            rules_version=comparison.rules_version,
            insights=[
                ComparisonInsightResponse.from_domain(insight)
                for insight in comparison.insights
            ],
            audits=[
                SourceAuditResponse.from_domain(audit) for audit in comparison.audits
            ],
        )


def get_comparison_service(request: Request) -> LiveHomeComparisonService:
    return cast(LiveHomeComparisonService, request.app.state.comparison_service)


@router.post("/live", response_model=LiveHomeComparisonResponse)
async def compare_homes(
    request: Request,
    payload: LiveComparisonRequest,
) -> LiveHomeComparisonResponse:
    comparison = await get_comparison_service(request).compare(
        tuple(payload.address_ids)
    )
    return LiveHomeComparisonResponse.from_domain(comparison)
