from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NeighborhoodProperties(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bu_code: str
    bu_naam: str
    wk_code: str
    wk_naam: str
    gm_code: str
    gm_naam: str
    jaar: str


class ProvinceProperties(BaseModel):
    model_config = ConfigDict(extra="ignore")

    statcode: str
    statnaam: str
    jaarcode: int
    rubriek: Literal["provincie"]


class NeighborhoodFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Feature"]
    id: UUID
    properties: NeighborhoodProperties


class ProvinceFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Feature"]
    id: UUID
    properties: ProvinceProperties


class NeighborhoodCollection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["FeatureCollection"]
    timestamp: datetime = Field(alias="timeStamp")
    features: list[NeighborhoodFeature]
    number_returned: int = Field(alias="numberReturned")

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class ProvinceCollection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["FeatureCollection"]
    timestamp: datetime = Field(alias="timeStamp")
    features: list[ProvinceFeature]
    number_returned: int = Field(alias="numberReturned")

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value
