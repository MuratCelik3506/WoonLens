from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl
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
    http_connect_timeout_seconds: float = Field(default=2.0, gt=0)
    http_read_timeout_seconds: float = Field(default=5.0, gt=0)
    http_write_timeout_seconds: float = Field(default=2.0, gt=0)
    http_pool_timeout_seconds: float = Field(default=2.0, gt=0)
    address_suggestion_limit: int = Field(default=8, ge=1, le=10)


@lru_cache
def get_settings() -> Settings:
    """Build settings once at the application boundary."""
    return Settings()
