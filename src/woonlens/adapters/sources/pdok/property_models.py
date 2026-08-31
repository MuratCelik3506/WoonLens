from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResidentialUnitProperties(BaseModel):
    model_config = ConfigDict(extra="ignore")

    identificatie: str
    status: str | None
    gebruiksdoel: str | None
    oppervlakte: int | None
    pand_hrefs: list[str] | None = Field(alias="pand.href")


class ResidentialUnitFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Feature"]
    id: UUID
    properties: ResidentialUnitProperties


class ResidentialUnitCollection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["FeatureCollection"]
    timestamp: datetime = Field(alias="timeStamp")
    features: list[ResidentialUnitFeature]
    number_returned: int = Field(alias="numberReturned")

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class BuildingProperties(BaseModel):
    model_config = ConfigDict(extra="ignore")

    identificatie: str
    status: str | None
    bouwjaar: int | None
    gebruiksdoel: str | None
    aantal_verblijfsobjecten: int | None


class BuildingFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Feature"]
    id: UUID
    properties: BuildingProperties
