from collections.abc import Callable
from datetime import UTC, datetime
from re import fullmatch

import httpx
from pydantic import TypeAdapter, ValidationError

from woonlens.adapters.sources.ep_online.models import EnergyRegistrationRecord
from woonlens.application.errors import (
    EnergyRegistrationNotFoundError,
    SourceAuthenticationError,
    SourceConfigurationError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.energy import EnergyRegistration, EnergyRegistrationDetails


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EpOnlineEnergyRegistrationAdapter:
    """Read and select the current EP-Online registration for a BAG unit."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str | None,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._clock = clock

    async def fetch(self, bag_object_id: str) -> EnergyRegistrationDetails:
        if fullmatch(r"\d{16}", bag_object_id) is None or bag_object_id == "0" * 16:
            raise SourceContractError
        if not self._api_key:
            raise SourceConfigurationError
        try:
            response = await self._client.get(
                f"{self._base_url}/PandEnergielabel/AdresseerbaarObject/{bag_object_id}",
                headers={"Authorization": self._api_key},
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise SourceUnavailableError from exc
        self._raise_for_status(response)
        try:
            records = TypeAdapter(list[EnergyRegistrationRecord]).validate_python(
                response.json()
            )
        except (ValidationError, ValueError) as exc:
            raise SourceContractError from exc
        if any(record.bag_object_id != bag_object_id for record in records):
            raise SourceContractError
        now = self._clock()
        current = [
            record for record in records if record.valid_until.date() >= now.date()
        ]
        if not current:
            raise EnergyRegistrationNotFoundError
        selected = max(
            current,
            key=lambda record: record.registration_date.replace(tzinfo=None),
        )
        try:
            registration = EnergyRegistration(
                bag_object_id=selected.bag_object_id,
                bag_building_ids=tuple(selected.bag_building_ids or []),
                registration_date=selected.registration_date,
                inspection_date=selected.inspection_date,
                valid_until=selected.valid_until,
                assessment_type=selected.assessment_type,
                registration_status=selected.registration_status,
                building_class=selected.building_class,
                building_type=selected.building_type,
                building_subtype=selected.building_subtype,
                construction_year=selected.construction_year,
                thermal_zone_area_m2=selected.thermal_zone_area_m2,
                energy_class=selected.energy_class,
                energy_demand_kwh_m2_year=selected.energy_demand,
                primary_fossil_energy_kwh_m2_year=selected.primary_fossil_energy,
                renewable_energy_share_pct=selected.renewable_energy_share,
                calculated_co2_kg_m2_year=selected.calculated_co2,
                calculated_energy_use_kwh_m2_year=selected.calculated_energy_use,
            )
        except ValueError as exc:
            raise SourceContractError from exc
        return EnergyRegistrationDetails(
            registration,
            SourceMetadata(
                "RVO / EP-Online",
                "EP-Online energy performance registrations",
                now,
                "EP-Online Terms of Use",
            ),
        )

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code == 404:
            raise EnergyRegistrationNotFoundError
        if response.status_code in {401, 403}:
            raise SourceAuthenticationError
        if response.status_code == 429:
            raise SourceRateLimitedError
        if response.status_code >= 500:
            raise SourceUnavailableError
        if response.is_error:
            raise SourceContractError
