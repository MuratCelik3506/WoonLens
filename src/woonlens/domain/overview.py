from dataclasses import dataclass

from woonlens.domain.addresses import ResolvedAddress
from woonlens.domain.administrative import AdministrativeContext
from woonlens.domain.energy import EnergyRegistrationDetails
from woonlens.domain.indicators import NeighborhoodIndicators
from woonlens.domain.property import PropertyDetails

SECTIONS = {
    "property",
    "energy_registration",
    "administrative_context",
    "neighborhood_indicators",
}


@dataclass(frozen=True, slots=True)
class UnavailableSection:
    """A safe explanation for one optional overview section."""

    section: str
    reason: str

    def __post_init__(self) -> None:
        if self.section not in SECTIONS or not self.reason:
            raise ValueError("unavailable section and reason must be valid")


@dataclass(frozen=True, slots=True)
class HomeOverview:
    """One transient composition of live official home facts."""

    address: ResolvedAddress
    property: PropertyDetails | None
    energy_registration: EnergyRegistrationDetails | None
    administrative_context: AdministrativeContext | None
    neighborhood_indicators: NeighborhoodIndicators | None
    unavailable_sections: tuple[UnavailableSection, ...]

    def __post_init__(self) -> None:
        names = [item.section for item in self.unavailable_sections]
        if len(names) != len(set(names)):
            raise ValueError("unavailable sections must be unique")
        values = {
            "property": self.property,
            "energy_registration": self.energy_registration,
            "administrative_context": self.administrative_context,
            "neighborhood_indicators": self.neighborhood_indicators,
        }
        if any(values[name] is not None for name in names):
            raise ValueError("an unavailable section cannot also contain data")
