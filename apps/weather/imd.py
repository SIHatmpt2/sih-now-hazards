"""India Meteorological Department API adapter."""
from __future__ import annotations

from datetime import UTC, datetime

import httpx

from apps.core.config import get_settings
from apps.weather.schemas import WeatherPoint, WeatherResponse


class IMDProvider:
    """Fetch current observations from the official IMD API."""

    name = "imd"

    def __init__(self):
        self.settings = get_settings()
        self._mapping_cache: list[dict] | None = None
        self._mapping_fetched_at: datetime | None = None

    @property
    def configured(self) -> bool:
        return bool(self.settings.imd_api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.settings.imd_api_key or "",
            "Accept": "application/json",
        }

    @staticmethod
    def _float(value):
        if value in (None, ""):
            return None
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int(value):
        value = IMDProvider._float(value)
        return int(value) if value is not None else None

    @staticmethod
    def _records(payload) -> list[dict]:
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            for key in ("data", "stations", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
            return [payload]
        return []

    async def _get(self, path: str, params: dict | None = None):
        if not self.configured:
            raise RuntimeError("IMD_API_KEY is not configured")

        async with httpx.AsyncClient(
            base_url=self.settings.imd_api_base_url.rstrip("/"),
            timeout=self.settings.request_timeout_seconds,
            headers=self._headers(),
        ) as client:
            response = await client.get(path, params=params)
            if response.status_code in (401, 403):
                raise RuntimeError(
                    f"IMD authentication/authorization failed ({response.status_code})"
                )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and payload.get("error"):
                raise RuntimeError(f"IMD API error: {payload['error']}")
            return payload

    async def _mapping(self) -> list[dict]:
        now = datetime.now(UTC)
        if (
            self._mapping_cache is not None
            and self._mapping_fetched_at is not None
            and (now - self._mapping_fetched_at).total_seconds() < 86400
        ):
            return self._mapping_cache

        payload = await self._get("/api/v1/cityforecast_mapping")
        records = self._records(payload)
        usable = []
        for row in records:
            lat = self._float(row.get("Latitude", row.get("latitude")))
            lon = self._float(
                row.get("Longitude", row.get("longitude", row.get("lng")))
            )
            code = row.get("Station_Code", row.get("station_code", row.get("id")))
            if code and lat is not None and lon is not None:
                usable.append(
                    {
                        "station_code": str(code),
                        "name": str(
                            row.get("Station_Name")
                            or row.get("station_name")
                            or row.get("name")
                            or code
                        ),
                        "latitude": lat,
                        "longitude": lon,
                    }
                )

        if not usable:
            raise RuntimeError("IMD cityforecast_mapping returned no usable stations")

        self._mapping_cache = usable
        self._mapping_fetched_at = now
        return usable

    async def _nearest_station(self, latitude: float, longitude: float) -> dict:
        stations = await self._mapping()

        # Equirectangular distance is sufficient for selecting the nearest
        # station among the IMD city-station catalogue at this scale.
        import math

        lat0 = math.radians(latitude)
        best = None
        best_distance = float("inf")
        for station in stations:
            dlat = math.radians(station["latitude"] - latitude)
            dlon = math.radians(station["longitude"] - longitude)
            x = dlon * math.cos(lat0)
            distance = x * x + dlat * dlat
            if distance < best_distance:
                best_distance = distance
                best = station

        if best is None:
            raise RuntimeError("No IMD station could be resolved")
        return best

    @staticmethod
    def _observation_timestamp(row: dict) -> datetime:
        date_value = str(row.get("Date of Observation") or "").strip()
        time_value = str(row.get("Time of Observation") or "").strip()
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(
                    f"{date_value} {time_value}", fmt
                ).replace(tzinfo=UTC)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(date_value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return datetime.now(UTC)

    async def fetch(self, latitude: float, longitude: float) -> WeatherResponse:
        station = await self._nearest_station(latitude, longitude)
        payload = await self._get(
            "/api/v1/current_wx",
            {"id": station["station_code"]},
        )
        rows = self._records(payload)
        if not rows:
            raise RuntimeError("IMD current_wx returned no observations")

        row = rows[0]
        observed_at = self._observation_timestamp(row)
        current = WeatherPoint(
            timestamp=observed_at,
            temperature_c=self._float(row.get("Temperature")),
            humidity_pct=self._float(row.get("Humidity")),
            precipitation_mm=self._float(row.get("Last 24 hrs Rainfall")),
            rain_mm=self._float(row.get("Last 24 hrs Rainfall")),
            cloud_cover_pct=(
                self._float(row.get("Nebulosity")) * 12.5
                if self._float(row.get("Nebulosity")) is not None
                else None
            ),
            wind_speed_kmh=self._float(row.get("Wind Speed")),
            wind_direction_deg=self._float(row.get("Wind Direction")),
            weather_code=self._int(row.get("Weather Code")),
        )
        return WeatherResponse(
            latitude=latitude,
            longitude=longitude,
            provider=self.name,
            fetched_at=datetime.now(UTC),
            current=current,
            hourly=[],
            warnings=[
                f"IMD station: {station['name']} ({station['station_code']})"
            ],
        )
