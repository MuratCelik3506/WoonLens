from pydantic import BaseModel, ConfigDict, Field


class MeasureCode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    identifier: str = Field(alias="Identifier")
    title: str = Field(alias="Title")
    unit: str = Field(alias="Unit")


class Observation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    measure: str = Field(alias="Measure")
    value: float | None = Field(alias="Value")
    value_attribute: str = Field(alias="ValueAttribute")
    neighborhood_code: str = Field(alias="WijkenEnBuurten")


class MeasureCodeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    context: str = Field(alias="@odata.context")
    value: list[MeasureCode]
    next_link: str | None = Field(default=None, alias="@odata.nextLink")


class ObservationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    context: str = Field(alias="@odata.context")
    value: list[Observation]
    next_link: str | None = Field(default=None, alias="@odata.nextLink")
