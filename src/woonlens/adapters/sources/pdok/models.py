from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PointGeometry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Point"]
    coordinates: tuple[float, float]

    @field_validator("coordinates")
    @classmethod
    def coordinates_are_crs84(cls, value: tuple[float, float]) -> tuple[float, float]:
        longitude, latitude = value
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValueError("coordinates must be valid CRS84 longitude and latitude")
        return value


class LocationProperties(BaseModel):
    model_config = ConfigDict(extra="ignore")

    collection_id: Literal["adres"]
    collection_version: Literal[1]
    display_name: str


class LocationFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Feature"]
    id: UUID
    properties: LocationProperties
    geometry: PointGeometry


class LocationSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["FeatureCollection"]
    timestamp: datetime = Field(alias="timeStamp")
    features: list[LocationFeature]
    numberReturned: int

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class BagAddressProperties(BaseModel):
    model_config = ConfigDict(extra="ignore")

    identificatie: str
    adresseerbaar_object_identificatie: str
    adresseerbaar_object_type: str
    openbare_ruimte_naam: str
    huisnummer: str
    huisletter: str | None
    toevoeging: str | None
    postcode: str
    woonplaats_naam: str


class BagAddressFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Feature"]
    id: UUID
    properties: BagAddressProperties
    geometry: PointGeometry
