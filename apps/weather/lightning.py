"""AccuWeather Lightning API adapter.

Current lightning is a separate AccuWeather product from Core Weather.
It uses the same Bearer API-key authentication but may require Lightning
entitlement on the account.
"""
from __future__ import annotations

import math
from datetime import UTC, datetime

import httpx

from apps.core.config import get_settings
from apps.weather.schemas import LightningResponse


class AccuWeatherLightningProvider:
    name = "accuweather-lightning"

    def __init__(self):
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.accuweather_lightning_api_key or self.settings.accuweather_api_key)

    @property
    def api_key(self) -> str | None:
        return self.settings.accuweather_lightning_api_key or self.settings.accuweather_api_key

    async def fetch(
        self,
        latitude: float,
        longitude: float,
        interval_minutes: int = 15,
        radius_km: float = 25.0,
    ) -> LightningResponse:
        if not self.configured:
            raise RuntimeError("No AccuWeather Lightning API key is configured")

        interval_minutes = interval_minutes if interval_minutes in (5, 15, 30, 60, 120) else 15
        radius_km = max(5.0, min(radius_km, 100.0))

        lat_delta = radius_km / 111.32
        lon_delta = radius_km / max(1e-6, 111.32 * math.cos(math.radians(latitude)))
        upper_left = f"{latitude + lat_delta:.4f},{longitude - lon_delta:.4f}"
        lower_right = f"{latitude - lat_delta:.4f},{longitude + lon_delta:.4f}"

        headers = {
            "Authorization": f"Bearer {self.api_key or ''}",
            "Accept": "application/geo+json, application/json",
            "Accept-Encoding": "gzip,deflate",
        }

        async with httpx.AsyncClient(
            base_url=self.settings.accuweather_api_base_url.rstrip("/"),
            timeout=self.settings.request_timeout_seconds,
            headers=headers,
        ) as client:
            response = await client.get(
                f"/lightning/v1/{interval_minutes}min/geoposition/points.geojson",
                params={"upperLeft": upper_left, "lowerRight": lower_right},
            )
            if response.status_code in (401, 403):
                raise RuntimeError(
                    f"AccuWeather Lightning authentication/authorization failed ({response.status_code}); "
                    "the Lightning product may not be enabled for this key"
                )
            response.raise_for_status()
            payload = response.json()

        features = payload.get("features") if isinstance(payload, dict) else []
        features = features if isinstance(features, list) else []
        currents = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                continue
            try:
                current = float(properties.get("peakCurrent"))
            except (TypeError, ValueError):
                current = None
            if current is not None:
                currents.append(abs(current))

        # Use the requested bounding-box area for a transparent density metric.
        width_km = 2 * radius_km
        height_km = 2 * radius_km
        area_km2 = width_km * height_km
        strike_count = len(features)

        return LightningResponse(
            provider=self.name,
            fetched_at=datetime.now(UTC),
            interval_minutes=interval_minutes,
            radius_km=radius_km,
            strike_count=strike_count,
            peak_current_a=max(currents) if currents else None,
            flash_rate_per_min=strike_count / interval_minutes,
            density_per_km2=strike_count / area_km2,
        )
