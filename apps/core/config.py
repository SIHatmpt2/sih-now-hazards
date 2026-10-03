from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "SkyIntel"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://skyintel:skyintel@localhost:5433/skyintel"
    redis_url: str = "redis://localhost:6380/0"
    celery_broker_url: str = "redis://localhost:6380/1"
    celery_result_backend: str = "redis://localhost:6380/2"

    s3_endpoint_url: str = "http://localhost:9001"
    s3_access_key_id: str = "skyintel"
    s3_secret_access_key: str = "skyintel123"
    s3_bucket: str = "skyintel-data"
    s3_region: str = "us-east-1"

    # Weather provider selection.
    # Keep "open-meteo" until the IMD adapter is enabled in the runtime.
    weather_provider: str = "imd"
    secondary_weather_provider: str = "accuweather"

    # IMD official data access.
    imd_api_base_url: str = "https://api.imd.gov.in"
    imd_api_key: str | None = None

    # AccuWeather Core Weather API.
    accuweather_api_base_url: str = "https://dataservice.accuweather.com"
    accuweather_api_key: str | None = None
    accuweather_location_key_cache_ttl_seconds: int = Field(86400, ge=300, le=604800)

    # Existing generic weather settings retained for provider adapters.
    weather_api_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_api_key: str | None = None

    # Satellite / radar provider configuration.
    satellite_provider: str = "imd"
    satellite_api_base_url: str = "https://api.imd.gov.in"
    satellite_api_key: str | None = None
    radar_provider: str = "rainviewer"
    radar_api_base_url: str = "https://api.rainviewer.com/public"

    # Lightning data source.
    lightning_provider: str = "imd"
    lightning_api_base_url: str = "https://api.imd.gov.in"
    lightning_api_key: str | None = None

    request_timeout_seconds: float = Field(15.0, ge=2, le=60)
    weather_cache_ttl_seconds: int = Field(300, ge=0, le=3600)
    max_weather_age_minutes: int = Field(90, ge=1, le=1440)

    model_version: str = "baseline-v1"
    model_manifest_path: str = "apps/Models/manifest.json"
    risk_threshold_low: float = Field(0.25, ge=0, le=1)
    risk_threshold_moderate: float = Field(0.50, ge=0, le=1)
    risk_threshold_high: float = Field(0.75, ge=0, le=1)

    persist_predictions: bool = True
    enable_raw_object_storage: bool = True
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:8001,http://127.0.0.1:8001"

    @property
    def cors_origin_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings():
    return Settings()
