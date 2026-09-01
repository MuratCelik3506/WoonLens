from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from woonlens.adapters.reports.pdf import ReportLabPdfRenderer
from woonlens.adapters.sources.cbs.client import CbsAdministrativeContextAdapter
from woonlens.adapters.sources.cbs.statline_client import CbsStatlineIndicatorsAdapter
from woonlens.adapters.sources.ep_online.client import EpOnlineEnergyRegistrationAdapter
from woonlens.adapters.sources.pdok.client import (
    PdokBagAddressAdapter,
    PdokLocationSearchAdapter,
)
from woonlens.adapters.sources.pdok.property_client import PdokBagPropertyAdapter
from woonlens.application.errors import WoonLensError
from woonlens.application.ports.reports import PdfReportRenderer
from woonlens.application.services.addresses import AddressService
from woonlens.application.services.administrative import AdministrativeContextService
from woonlens.application.services.comparison import LiveHomeComparisonService
from woonlens.application.services.energy import EnergyRegistrationService
from woonlens.application.services.indicators import NeighborhoodIndicatorsService
from woonlens.application.services.overview import HomeOverviewService
from woonlens.application.services.property import PropertyDetailsService
from woonlens.application.services.reporting import ComparisonEvidenceReportService
from woonlens.bootstrap.settings import Settings, get_settings
from woonlens.entrypoints.api.addresses import router as addresses_router
from woonlens.entrypoints.api.comparisons import router as comparisons_router
from woonlens.entrypoints.api.health import router as health_router
from woonlens.entrypoints.api.problems import woonlens_error_handler
from woonlens.entrypoints.api.reports import router as reports_router


def create_app(
    settings: Settings | None = None,
    address_service: AddressService | None = None,
    administrative_context_service: AdministrativeContextService | None = None,
    neighborhood_indicators_service: NeighborhoodIndicatorsService | None = None,
    property_details_service: PropertyDetailsService | None = None,
    energy_registration_service: EnergyRegistrationService | None = None,
    home_overview_service: HomeOverviewService | None = None,
    comparison_service: LiveHomeComparisonService | None = None,
    report_service: ComparisonEvidenceReportService | None = None,
    pdf_report_renderer: PdfReportRenderer | None = None,
) -> FastAPI:
    """Create the HTTP application with explicit configuration."""
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if address_service is not None:
            app.state.address_service = address_service
            if administrative_context_service is not None:
                app.state.administrative_context_service = (
                    administrative_context_service
                )
            if neighborhood_indicators_service is not None:
                app.state.neighborhood_indicators_service = (
                    neighborhood_indicators_service
                )
            if property_details_service is not None:
                app.state.property_details_service = property_details_service
            if energy_registration_service is not None:
                app.state.energy_registration_service = energy_registration_service
            if home_overview_service is not None:
                app.state.home_overview_service = home_overview_service
            if comparison_service is not None:
                app.state.comparison_service = comparison_service
                app.state.report_service = (
                    report_service
                    or ComparisonEvidenceReportService(comparison_service)
                )
                app.state.pdf_report_renderer = (
                    pdf_report_renderer or ReportLabPdfRenderer()
                )
            yield
            return

        timeout = httpx.Timeout(
            connect=resolved_settings.http_connect_timeout_seconds,
            read=resolved_settings.http_read_timeout_seconds,
            write=resolved_settings.http_write_timeout_seconds,
            pool=resolved_settings.http_pool_timeout_seconds,
        )
        async with httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": "WoonLens/0.1"},
        ) as client:
            bag_adapter = PdokBagAddressAdapter(
                client,
                str(resolved_settings.pdok_bag_api_url),
            )
            app.state.address_service = AddressService(
                PdokLocationSearchAdapter(
                    client,
                    str(resolved_settings.pdok_location_api_url),
                ),
                bag_adapter,
                suggestion_limit=resolved_settings.address_suggestion_limit,
            )
            administrative_adapter = CbsAdministrativeContextAdapter(
                client,
                str(resolved_settings.pdok_cbs_neighborhoods_api_url),
                str(resolved_settings.pdok_cbs_regions_api_url),
                dataset_year=resolved_settings.cbs_administrative_dataset_year,
            )
            indicators_adapter = CbsStatlineIndicatorsAdapter(
                client,
                str(resolved_settings.cbs_statline_api_url),
                dataset_id=resolved_settings.cbs_neighborhood_indicators_dataset_id,
                dataset_year=resolved_settings.cbs_neighborhood_indicators_dataset_year,
            )
            property_adapter = PdokBagPropertyAdapter(
                client,
                str(resolved_settings.pdok_bag_api_url),
                max_related_buildings=resolved_settings.bag_max_related_buildings,
            )
            secret = resolved_settings.ep_online_api_key
            energy_adapter = EpOnlineEnergyRegistrationAdapter(
                client,
                str(resolved_settings.ep_online_api_url),
                secret.get_secret_value() if secret is not None else None,
            )
            app.state.administrative_context_service = AdministrativeContextService(
                bag_adapter, administrative_adapter
            )
            app.state.neighborhood_indicators_service = NeighborhoodIndicatorsService(
                bag_adapter,
                administrative_adapter,
                indicators_adapter,
            )
            app.state.property_details_service = PropertyDetailsService(
                bag_adapter,
                property_adapter,
            )
            app.state.energy_registration_service = EnergyRegistrationService(
                bag_adapter,
                energy_adapter,
            )
            overview_service = HomeOverviewService(
                bag_adapter,
                property_adapter,
                energy_adapter,
                administrative_adapter,
                indicators_adapter,
            )
            app.state.home_overview_service = overview_service
            live_comparison_service = LiveHomeComparisonService(overview_service)
            app.state.comparison_service = live_comparison_service
            app.state.report_service = ComparisonEvidenceReportService(
                live_comparison_service
            )
            app.state.pdf_report_renderer = ReportLabPdfRenderer()
            yield

    app = FastAPI(
        title="WoonLens API",
        version="0.1.0",
        docs_url="/docs" if resolved_settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.add_exception_handler(WoonLensError, woonlens_error_handler)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(addresses_router, prefix="/api/v1")
    app.include_router(comparisons_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")
    return app


__all__ = ["create_app"]
