"""AccuWeather Core Weather API adapter."""
from __future__ import annotations

from datetime import UTC, datetime

import httpx

from apps.core.config import get_settings
from apps.weather.schemas import WeatherPoint, WeatherResponse


class AccuWeatherProvider:
    name = "accuweather"

    def __init__(self):
        self.settings = get_settings()
        self._location_cache: dict[tuple[float, float], tuple[str, datetime]] = {}

    @property
    def configured(self) -> bool:
        return bool(self.settings.accuweather_api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.accuweather_api_key or ''}",
            "Accept": "application/json",
            "Accept-Encoding": "gzip,deflate",
        }

    @staticmethod
    def _float(value):
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _metric(obj):
        if not isinstance(obj, dict):
            return None
        value = obj.get("Metric")
        return AccuWeatherProvider._float(value.get("Value")) if isinstance(value, dict) else None

    @staticmethod
    def _timestamp(value: str | None) -> datetime:
        if not value:
            return datetime.now(UTC)
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return datetime.now(UTC)

    async def _get(self, path: str, params: dict | None = None):
        if not self.configured:
            raise RuntimeError("ACCUWEATHER_API_KEY is not configured")

        async with httpx.AsyncClient(
            base_url=self.settings.accuweather_api_base_url.rstrip("/"),
            timeout=self.settings.request_timeout_seconds,
            headers=self._headers(),
        ) as client:
            response = await client.get(path, params=params)
            if response.status_code in (401, 403):
                raise RuntimeError(
                    f"AccuWeather authentication/authorization failed ({response.status_code})"
                )
            response.raise_for_status()
            return response.json()

    async def _location_key(self, latitude: float, longitude: float) -> str:
        cache_key = (round(latitude, 3), round(longitude, 3))
        now = datetime.now(UTC)
        cached = self._location_cache.get(cache_key)
        if cached and (now - cached[1]).total_seconds() < self.settings.accuweather_location_key_cache_ttl_seconds:
            return cached[0]

        payload = await self._get(
            "/locations/v1/geoposition/search",
            {"q": f"{latitude:.3f},{longitude:.3f}", "language": "en-us", "topLevel": "true"},
        )
        # AccuWeather's geoposition endpoint returns a JSON array of location
        # objects. Accept the documented list response and retain support for
        # a single object in case the provider returns one.
        if isinstance(payload, list):
            payload = payload[0] if payload and isinstance(payload[0], dict) else None

        if not isinstance(payload, dict) or not payload.get("Key"):
            raise RuntimeError("AccuWeather geoposition lookup returned no location key")

        key = str(payload["Key"])
        self._location_cache[cache_key] = (key, now)
        return key

    @staticmethod
    def _wind_values(obj: dict | None):
        if not isinstance(obj, dict):
            return None, None
        speed = AccuWeatherProvider._metric(obj.get("Speed"))
        direction = obj.get("Direction") if isinstance(obj.get("Direction"), dict) else {}
        degrees = AccuWeatherProvider._float(direction.get("Degrees"))
        return speed, degrees

    def _point_from_current(self, row: dict) -> WeatherPoint:
        wind_speed, wind_direction = self._wind_values(row.get("Wind"))
        gust_speed, _ = self._wind_values(row.get("WindGust"))
        temperature = self._metric(row.get("Temperature"))
        return WeatherPoint(
            timestamp=self._timestamp(row.get("LocalObservationDateTime")),
            temperature_c=temperature,
            humidity_pct=self._float(row.get("RelativeHumidity")),
            precipitation_mm=self._metric(row.get("Precip1hr")),
            rain_mm=None,
            cloud_cover_pct=self._float(row.get("CloudCover")),
            wind_speed_kmh=wind_speed,
            wind_direction_deg=wind_direction,
            wind_gust_kmh=gust_speed,
        )

    def _point_from_hourly(self, row: dict) -> WeatherPoint:
        wind_speed, wind_direction = self._wind_values(row.get("Wind"))
        gust_speed, _ = self._wind_values(row.get("WindGust"))
        rain = self._metric(row.get("Rain"))
        total_liquid = self._metric(row.get("TotalLiquid"))
        return WeatherPoint(
            timestamp=self._timestamp(row.get("DateTime")),
            temperature_c=self._metric(row.get("Temperature")),
            humidity_pct=self._float(row.get("RelativeHumidity")),
            precipitation_probability_pct=self._float(row.get("PrecipitationProbability")),
            precipitation_mm=total_liquid,
            rain_mm=rain,
            cloud_cover_pct=self._float(row.get("CloudCover")),
            wind_speed_kmh=wind_speed,
            wind_direction_deg=wind_direction,
            wind_gust_kmh=gust_speed,
        )

    async def fetch(self, latitude: float, longitude: float, hours: int = 6) -> WeatherResponse:
        key = await self._location_key(latitude, longitude)
        current_payload, hourly_payload = await self._get(
            f"/currentconditions/v1/{key}", {"details": "true"}
        ), await self._get(
            f"/forecasts/v1/hourly/12hour/{key}",
            {"language": "en-us", "metric": "true", "details": "true"},
        )

        if not isinstance(current_payload, list) or not current_payload:
            raise RuntimeError("AccuWeather current conditions returned no data")
        hourly_rows = hourly_payload if isinstance(hourly_payload, list) else []

        points = [self._point_from_hourly(row) for row in hourly_rows[: max(1, hours)]]
        return WeatherResponse(
            latitude=latitude,
            longitude=longitude,
            provider=self.name,
            fetched_at=datetime.now(UTC),
            current=self._point_from_current(current_payload[0]),
            hourly=points,
        )
