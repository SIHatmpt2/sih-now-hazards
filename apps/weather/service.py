"""Weather provider orchestration and normalization."""
from __future__ import annotations

import asyncio
from datetime import UTC

from apps.core.cache import RedisCache
from apps.core.config import get_settings
from apps.core.schemas import FeatureBundle
from apps.weather.accuweather import AccuWeatherProvider
from apps.weather.imd import IMDProvider
from apps.weather.open_meteo import OpenMeteoProvider
from apps.weather.lightning import AccuWeatherLightningProvider
from apps.weather.schemas import WeatherPoint, WeatherResponse


class WeatherService:
    def __init__(self):
        self.settings = get_settings()
        self.imd = IMDProvider()
        self.accuweather = AccuWeatherProvider()
        self.open_meteo = OpenMeteoProvider()
        self.lightning = AccuWeatherLightningProvider()
        self.cache = RedisCache()

    async def get(self, latitude: float, longitude: float, hours: int = 6):
        key = f"weather:v3:{latitude:.4f}:{longitude:.4f}:{hours}"
        cached = await self.cache.get_json(key)
        if cached:
            return WeatherResponse.model_validate(cached)

        # Once either supplied paid/institutional key is present, use the
        # configured IMD + AccuWeather sources. Open-Meteo remains only as a
        # development fallback when neither key has been configured.
        use_configured_sources = self.imd.configured or self.accuweather.configured

        if use_configured_sources:
            results = await asyncio.gather(
                self.imd.fetch(latitude, longitude) if self.imd.configured else asyncio.sleep(0, result=None),
                self.accuweather.fetch(latitude, longitude, hours) if self.accuweather.configured else asyncio.sleep(0, result=None),
                return_exceptions=True,
            )
            imd_result, accuweather_result = results
            warnings: list[str] = []

            if isinstance(imd_result, Exception):
                warnings.append(f"IMD unavailable: {imd_result}")
                imd_result = None
            if isinstance(accuweather_result, Exception):
                warnings.append(f"AccuWeather unavailable: {accuweather_result}")
                accuweather_result = None

            current = None
            hourly = []
            providers = []
            lightning_result = None

            if isinstance(imd_result, WeatherResponse):
                current = imd_result.current
                providers.append("imd")
                warnings.extend(imd_result.warnings)

            if isinstance(accuweather_result, WeatherResponse):
                providers.append("accuweather")
                # AccuWeather provides the hourly forecast used by the
                # dashboard's six-hour forecast window.
                hourly = accuweather_result.hourly
                if current is None:
                    current = accuweather_result.current

            if self.lightning.configured:
                try:
                    lightning_result = await self.lightning.fetch(latitude, longitude)
                except Exception as exc:
                    warnings.append(f"AccuWeather Lightning unavailable: {exc}")

            if current is None:
                raise RuntimeError(
                    "Neither configured weather provider returned usable data"
                )

            provider_name = "+".join(providers)
            response = WeatherResponse(
                latitude=latitude,
                longitude=longitude,
                provider=provider_name,
                fetched_at=(
                    imd_result.fetched_at
                    if isinstance(imd_result, WeatherResponse)
                    else accuweather_result.fetched_at
                ),
                current=current,
                hourly=hourly,
                lightning=lightning_result,
                warnings=list(dict.fromkeys(warnings)),
            )
            await self.cache.set_json(
                key,
                response.model_dump(mode="json"),
                self.settings.weather_cache_ttl_seconds,
            )
            return response

        if self.settings.weather_provider != "open-meteo":
            raise RuntimeError(
                f"No configured IMD/AccuWeather source and WEATHER_PROVIDER is "
                f"{self.settings.weather_provider!r}"
            )

        result = await self.open_meteo.fetch(latitude, longitude, hours)
        await self.cache.set_json(
            key,
            result.model_dump(mode="json"),
            self.settings.weather_cache_ttl_seconds,
        )
        return result


def cloud_type_from_weather(p: WeatherPoint):
    if p.weather_code in (95, 96, 99):
        return "Deep Convective"
    cloud_cover = p.cloud_cover_pct or 0
    if cloud_cover >= 85:
        return "Deep Cloud Layer"
    if cloud_cover >= 60:
        return "Multi-layer Cloud"
    if cloud_cover >= 30:
        return "Broken Cloud"
    return "Partly Cloudy"


def point_to_features(p: WeatherPoint, latitude, longitude):
    ts = p.timestamp if p.timestamp.tzinfo else p.timestamp.replace(tzinfo=UTC)
    return FeatureBundle(
        latitude=latitude,
        longitude=longitude,
        observed_at=ts,
        temperature_c=p.temperature_c,
        humidity_pct=p.humidity_pct,
        precipitation_probability_pct=p.precipitation_probability_pct,
        precipitation_mm=p.precipitation_mm,
        rain_mm=p.rain_mm,
        showers_mm=p.showers_mm,
        cloud_cover_pct=p.cloud_cover_pct,
        wind_speed_kmh=p.wind_speed_kmh,
        wind_direction_deg=p.wind_direction_deg,
        wind_gust_kmh=p.wind_gust_kmh,
        weather_code=p.weather_code,
        cloud_direction_deg=p.wind_direction_deg,
        cloud_velocity_kmh=p.wind_speed_kmh,
        cloud_type=cloud_type_from_weather(p),
        downburst_velocity_kmh=p.wind_gust_kmh,
        monsoon_status="Active" if ts.month in (6, 7, 8, 9) else "Off-season",
    )
