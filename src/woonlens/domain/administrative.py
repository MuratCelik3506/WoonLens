from dataclasses import dataclass

from woonlens.domain.addresses import SourceMetadata


@dataclass(frozen=True, slots=True)
class AdministrativeArea:
    """One official CBS administrative or statistical area."""

    code: str
    name: str

    def __post_init__(self) -> None:
        if not self.code or not self.name:
            raise ValueError("administrative area code and name are required")


@dataclass(frozen=True, slots=True)
class AdministrativeContext:
    """The official areas containing one resolved address coordinate."""

    neighborhood: AdministrativeArea | None
    district: AdministrativeArea | None
    municipality: AdministrativeArea | None
    province: AdministrativeArea | None
    sources: tuple[SourceMetadata, ...]

    def __post_init__(self) -> None:
        if not any(
            (self.neighborhood, self.district, self.municipality, self.province)
        ):
            raise ValueError("administrative context must contain at least one area")
        if not self.sources:
            raise ValueError("administrative context must contain provenance")
