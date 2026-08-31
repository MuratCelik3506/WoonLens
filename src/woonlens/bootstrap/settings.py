from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated process configuration."""

    model_config = SettingsConfigDict(
        env_prefix="WOONLENS_",
        env_file=None,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "production"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    pdok_location_api_url: HttpUrl = HttpUrl(
        "https://api.pdok.nl/kadaster/location-api/v1"
    )
    pdok_bag_api_url: HttpUrl = HttpUrl("https://api.pdok.nl/kadaster/bag/ogc/v2")
    pdok_cbs_neighborhoods_api_url: HttpUrl = HttpUrl(
        "https://api.pdok.nl/cbs/wijken-en-buurten-2026/ogc/v1"
    )
    pdok_cbs_regions_api_url: HttpUrl = HttpUrl(
        "https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1"
    )
    cbs_administrative_dataset_year: int = Field(default=2026, ge=2000, le=2100)
    cbs_statline_api_url: HttpUrl = HttpUrl("https://datasets.cbs.nl/odata/v1/CBS")
    cbs_neighborhood_indicators_dataset_id: str = "85984NED"
    cbs_neighborhood_indicators_dataset_year: int = Field(
        default=2024,
        ge=2000,
        le=2100,
    )
    http_connect_timeout_seconds: float = Field(default=2.0, gt=0)
    http_read_timeout_seconds: float = Field(default=5.0, gt=0)
    http_write_timeout_seconds: float = Field(default=2.0, gt=0)
    http_pool_timeout_seconds: float = Field(default=2.0, gt=0)
    address_suggestion_limit: int = Field(default=8, ge=1, le=10)
    bag_max_related_buildings: int = Field(default=10, ge=1, le=25)
    ep_online_api_url: HttpUrl = HttpUrl("https://public.ep-online.nl/api/v5")
    ep_online_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    """Build settings once at the application boundary."""
    return Settings()
