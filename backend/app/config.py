from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models import BoundingBox


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Secrets (required: startup fails if missing)
    opensky_client_id: str
    opensky_client_secret: str

    # Region: Sri Lanka and surrounding airspace (7x7 degrees = 2 API credits)
    region_lamin: float = 4.0
    region_lomin: float = 77.0
    region_lamax: float = 11.0
    region_lomax: float = 84.0

    # Polling behaviour
    poll_interval_s: float = Field(default=30.0, ge=5.0)
    poller_grace_period_s: float = Field(default=60.0, ge=0.0)
    http_timeout_s: float = Field(default=15.0, gt=0.0)

    # Which frontend origins may connect
    allowed_origins: list[str] = ["http://localhost:5173"]

    @property
    def region(self) -> BoundingBox:
        return BoundingBox(
            lamin=self.region_lamin,
            lomin=self.region_lomin,
            lamax=self.region_lamax,
            lomax=self.region_lomax,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
