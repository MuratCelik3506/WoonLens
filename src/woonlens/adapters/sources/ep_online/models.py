from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnergyRegistrationRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    registration_date: datetime = Field(alias="Registratiedatum")
    inspection_date: datetime | None = Field(default=None, alias="Opnamedatum")
    valid_until: datetime = Field(alias="Geldig_tot")
    assessment_type: str | None = Field(default=None, alias="Soort_opname")
    registration_status: str | None = Field(default=None, alias="Status")
    building_class: str | None = Field(default=None, alias="Gebouwklasse")
    building_type: str | None = Field(default=None, alias="Gebouwtype")
    building_subtype: str | None = Field(default=None, alias="Gebouwsubtype")
    bag_object_id: str = Field(alias="BAGVerblijfsobjectID")
    bag_building_ids: list[str] | None = Field(default=None, alias="BAGPandIDs")
    construction_year: int | None = Field(default=None, alias="Bouwjaar")
    thermal_zone_area_m2: float | None = Field(
        default=None, alias="Gebruiksoppervlakte_thermische_zone"
    )
    energy_class: str | None = Field(default=None, alias="Energieklasse")
    energy_demand: float | None = Field(default=None, alias="Energiebehoefte")
    primary_fossil_energy: float | None = Field(
        default=None, alias="PrimaireFossieleEnergie"
    )
    renewable_energy_share: float | None = Field(
        default=None, alias="Aandeel_hernieuwbare_energie"
    )
    calculated_co2: float | None = Field(default=None, alias="BerekendeCO2Emissie")
    calculated_energy_use: float | None = Field(
        default=None, alias="BerekendeEnergieverbruik"
    )
