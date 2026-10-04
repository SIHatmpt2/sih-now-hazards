"""Bhuvan/NRSC Lightning Portal adapter.

Uses the public OGC WMS service exposed by NRSC's Bhuvan Lightning
infrastructure. The service advertises the lightning layers used by the
portal, including hourly lightning and the lightning density grid.

The adapter never fabricates lightning observations. If the service cannot
return a queryable lightning response, the caller gets a controlled error.
"""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any

import httpx

from apps.core.config import get_settings
from apps.weather.schemas import LightningResponse


class _KeyValueHTMLParser(HTMLParser):
    """Extract simple two-column key/value tables from WMS HTML output."""
    def __init__(self):
        super().__init__()
        self.rows: list[list[str]] = []
        self._cells: list[str] | None = None
        self._cell_text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag == "tr":
            self._cells = []
        elif tag in ("td", "th") and self._cells is not None:
            self._cell_text = []

    def handle_data(self, data: str):
        if self._cells is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in ("td", "th") and self._cells is not None:
            self._cells.append(" ".join("".join(self._cell_text).split()))
            self._cell_text = []
        elif tag == "tr" and self._cells is not None:
            if self._cells:
                self.rows.append(self._cells)
            self._cells = None
            self._cell_text = []


def _parse_key_value_text(raw_text: str) -> list[dict[str, Any]]:
    properties: dict[str, Any] = {}
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^\s*([^:=\t]{2,80})\s*(?::|=|\t)\s*(.*?)\s*$", line)
        if match:
            key, value = match.groups()
            if key and value:
                properties[key.strip()] = value.strip()
    return [{"properties": properties}] if properties else []


def _parse_key_value_html(raw_text: str) -> list[dict[str, Any]]:
    parser = _KeyValueHTMLParser()
    parser.feed(raw_text)
    properties: dict[str, Any] = {}
    for row in parser.rows:
        if len(row) >= 2 and row[0] and row[1]:
            properties[row[0]] = row[1]
    return [{"properties": properties}] if properties else []


class BhuvanLightningProvider:
    name = "bhuvan-nrsc-lightning"
    preferred_layers = ("lighthourly", "grid")

    def __init__(self):
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return (
            self.settings.lightning_provider.strip().lower() == "bhuvan"
            and bool(self.settings.lightning_api_base_url.strip())
        )

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    @classmethod
    def _child_text(cls, element: ET.Element, name: str) -> str | None:
        target = name.lower()
        for child in list(element):
            if cls._local_name(child.tag) == target:
                value = (child.text or "").strip()
                return value or None
        return None

    @classmethod
    def _capability_layers(cls, xml_text: str) -> list[str]:
        root = ET.fromstring(xml_text)
        layers: list[str] = []
        for element in root.iter():
            if cls._local_name(element.tag) != "layer":
                continue
            name = cls._child_text(element, "name")
            if not name:
                continue
            queryable = str(element.attrib.get("queryable", "")).strip().lower()
            if queryable in ("1", "true") or not queryable:
                layers.append(name.strip())
        return layers

    @staticmethod
    def _normalise_key(value: str) -> str:
        return "".join(ch for ch in value.lower() if ch.isalnum())

    @classmethod
    def _first_number(cls, properties: dict[str, Any], aliases: tuple[str, ...]) -> float | None:
        wanted = {cls._normalise_key(alias) for alias in aliases}
        for key, value in properties.items():
            if cls._normalise_key(str(key)) not in wanted:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    @classmethod
    def _first_text(cls, properties: dict[str, Any], aliases: tuple[str, ...]) -> str | None:
        wanted = {cls._normalise_key(alias) for alias in aliases}
        for key, value in properties.items():
            if cls._normalise_key(str(key)) not in wanted:
                continue
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        candidate = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
            ):
                try:
                    parsed = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    parsed = None
            if parsed is None:
                return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @classmethod
    def _json_features(cls, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, dict):
            features = payload.get("features")
            if isinstance(features, list):
                return [item for item in features if isinstance(item, dict)]
            feature = payload.get("feature")
            if isinstance(feature, dict):
                return [feature]
        return []

    @classmethod
    def _text_features(cls, raw_text: str) -> list[dict[str, Any]]:
        return _parse_key_value_text(raw_text)

    @classmethod
    def _html_features(cls, raw_text: str) -> list[dict[str, Any]]:
        return _parse_key_value_html(raw_text)

    @classmethod
    def _xml_features(cls, raw_text: str) -> list[dict[str, Any]]:
        root = ET.fromstring(raw_text)
        if cls._local_name(root.tag) in ("serviceexceptionreport", "serviceexception"):
            return []
        results: list[dict[str, Any]] = []
        for member in root.iter():
            if cls._local_name(member.tag) not in ("featuremember", "featuremembers"):
                continue
            for feature in list(member):
                properties: dict[str, Any] = {}
                for child in feature.iter():
                    if child is feature:
                        continue
                    if list(child):
                        continue
                    value = (child.text or "").strip()
                    if value:
                        properties[cls._local_name(child.tag)] = value
                if properties:
                    results.append({"properties": properties})
        return results

    @staticmethod
    def _feature_coordinates(feature: dict[str, Any]) -> tuple[float, float] | None:
        geometry = feature.get("geometry")
        if isinstance(geometry, dict):
            coordinates = geometry.get("coordinates")
            if (
                isinstance(coordinates, (list, tuple))
                and len(coordinates) >= 2
                and all(isinstance(v, (int, float)) for v in coordinates[:2])
            ):
                lon, lat = float(coordinates[0]), float(coordinates[1])
                return lat, lon

        properties = feature.get("properties")
        if isinstance(properties, dict):
            lat = BhuvanLightningProvider._first_number(
                properties,
                ("latitude", "lat", "y"),
            )
            lon = BhuvanLightningProvider._first_number(
                properties,
                ("longitude", "lon", "lng", "x"),
            )
            if lat is not None and lon is not None:
                return lat, lon
        return None

    async def _get_feature_info(
        self,
        client: httpx.AsyncClient,
        layer: str,
        latitude: float,
        longitude: float,
        radius_km: float,
        info_format: str,
    ) -> tuple[list[dict[str, Any]], bool]:
        lat_delta = radius_km / 111.32
        lon_delta = radius_km / max(
            1e-6,
            111.32 * math.cos(math.radians(latitude)),
        )
        min_lon = longitude - lon_delta
        max_lon = longitude + lon_delta
        min_lat = latitude - lat_delta
        max_lat = latitude + lat_delta

        response = await client.get(
            "",
            params={
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetFeatureInfo",
                "LAYERS": layer,
                "QUERY_LAYERS": layer,
                "STYLES": "",
                "SRS": "EPSG:4326",
                "BBOX": f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}",
                "WIDTH": "256",
                "HEIGHT": "256",
                "X": "128",
                "Y": "128",
                "INFO_FORMAT": info_format,
                "FEATURE_COUNT": "100",
            },
        )
        response.raise_for_status()

        raw_text = response.text.lstrip()
        lowered = raw_text.lower()
        if "<serviceexception" in lowered or "<exceptionreport" in lowered or "serviceexceptionreport" in lowered:
            return [], False

        if info_format == "text/plain":
            features = cls._text_features(response.text)
            return features, bool(features)

        if info_format == "text/html":
            features = cls._html_features(response.text)
            return features, bool(features)

        if "json" in response.headers.get("content-type", "").lower() or info_format == "application/json":
            try:
                payload = response.json()
                return self._json_features(payload), True
            except (ValueError, TypeError):
                pass

        try:
            return self._xml_features(response.text), True
        except (ET.ParseError, ValueError):
            return [], False

    @classmethod
    def _normalise_result(
        cls,
        layer_features: list[tuple[str, list[dict[str, Any]]]],
        radius_km: float,
    ) -> LightningResponse:
        count: float | None = None
        density: float | None = None
        flash_rate: float | None = None
        peak_current: float | None = None
        intensity: str | None = None
        latest_observation: datetime | None = None
        latest_latitude: float | None = None
        latest_longitude: float | None = None
        count_layer: str | None = None

        for layer, features in layer_features:
            for feature in features:
                properties = feature.get("properties")
                if not isinstance(properties, dict):
                    properties = {}

                direct_count = cls._first_number(
                    properties,
                    (
                        "strike_count",
                        "flash_count",
                        "lightning_count",
                        "number_of_strikes",
                        "number_of_flashes",
                        "strikes",
                        "flashes",
                        "count",
                    ),
                )
                if direct_count is not None and (count is None or layer == "lighthourly"):
                    count = max(0.0, direct_count)
                    count_layer = layer

                direct_density = cls._first_number(
                    properties,
                    (
                        "lightning_density",
                        "strike_density",
                        "flash_density",
                        "density",
                        "flashes_per_km2",
                        "strikes_per_km2",
                    ),
                )
                if direct_density is not None:
                    density = max(0.0, direct_density)

                direct_rate = cls._first_number(
                    properties,
                    (
                        "flash_rate_per_min",
                        "flash_rate",
                        "lightning_flash_rate",
                        "strikes_per_min",
                        "flashes_per_min",
                    ),
                )
                if direct_rate is not None:
                    flash_rate = max(0.0, direct_rate)

                current = cls._first_number(
                    properties,
                    (
                        "peak_current",
                        "peak_current_a",
                        "current",
                        "current_a",
                        "amperage",
                    ),
                )
                if current is not None:
                    peak_current = max(peak_current or 0.0, abs(current))

                direct_intensity = cls._first_text(
                    properties,
                    (
                        "lightning_intensity",
                        "strike_intensity",
                        "intensity",
                        "intensity_category",
                        "category",
                        "class",
                    ),
                )
                if direct_intensity:
                    intensity = direct_intensity

                observation_text = cls._first_text(
                    properties,
                    (
                        "observation_time",
                        "latest_observation",
                        "timestamp",
                        "datetime",
                        "time",
                        "date_time",
                    ),
                )
                observation_time = cls._parse_datetime(observation_text)
                coordinates = cls._feature_coordinates(feature)
                if observation_time and (
                    latest_observation is None or observation_time > latest_observation
                ):
                    latest_observation = observation_time
                    if coordinates:
                        latest_latitude, latest_longitude = coordinates

        warnings: list[str] = []

        if density is None and count is not None and count_layer == "grid":
            density = count / 100.0
            warnings.append("Lightning density is derived from a 10 km x 10 km Bhuvan grid count.")

        if flash_rate is None and count is not None and count_layer == "lighthourly":
            flash_rate = count / 60.0
            warnings.append("Lightning flash rate is the hourly mean derived from the Bhuvan hourly strike count.")

        if count is None and density is None and flash_rate is None and peak_current is None and intensity is None:
            raise RuntimeError("Bhuvan Lightning returned no usable measurement attributes")

        strike_count = int(round(count)) if count is not None else 0

        return LightningResponse(
            provider=cls.name,
            fetched_at=datetime.now(UTC),
            interval_minutes=60,
            radius_km=radius_km,
            strike_count=strike_count,
            peak_current_a=peak_current,
            strike_intensity=intensity,
            latest_observation_time=latest_observation,
            latest_latitude=latest_latitude,
            latest_longitude=latest_longitude,
            flash_rate_per_min=flash_rate,
            density_per_km2=density,
            warnings=warnings,
        )

    async def fetch(
        self,
        latitude: float,
        longitude: float,
        interval_minutes: int = 60,
        radius_km: float | None = None,
    ) -> LightningResponse:
        if not self.configured:
            raise RuntimeError("Bhuvan Lightning provider is not configured")

        radius = (
            self.settings.lightning_radius_km
            if radius_km is None
            else radius_km
        )
        radius = max(5.0, min(float(radius), 100.0))

        base_url = self.settings.lightning_api_base_url.rstrip("/") + "/"
        async with httpx.AsyncClient(
            base_url=base_url,
            timeout=self.settings.request_timeout_seconds,
            follow_redirects=True,
            headers={"Accept": "application/json, application/xml, text/xml"},
        ) as client:
            capabilities = await client.get(
                "",
                params={
                    "SERVICE": "WMS",
                    "VERSION": "1.3.0",
                    "REQUEST": "GetCapabilities",
                },
            )
            capabilities.raise_for_status()

            try:
                available = self._capability_layers(capabilities.text)
            except (ET.ParseError, ValueError) as exc:
                raise RuntimeError("Bhuvan Lightning capabilities response is invalid") from exc

            layer_lookup = {name.lower(): name for name in available}
            selected_layers = [
                layer_lookup[name]
                for name in self.preferred_layers
                if name in layer_lookup
            ]
            if not selected_layers:
                raise RuntimeError(
                    "Bhuvan Lightning service does not expose a supported query layer"
                )

            results: list[tuple[str, list[dict[str, Any]]]] = []
            query_errors: list[str] = []
            successful_query = False

            for layer in selected_layers:
                try:
                    parsed = False
                    features: list[dict[str, Any]] = []

                    for info_format in (
                        "text/plain",
                        "text/html",
                        "application/vnd.ogc.gml",
                        "application/json",
                    ):
                        try:
                            candidate_features, candidate_parsed = await self._get_feature_info(
                                client,
                                layer,
                                latitude,
                                longitude,
                                radius,
                                info_format,
                            )
                        except Exception as exc:
                            query_errors.append(f"{layer} ({info_format}): {exc}")
                            continue

                        if candidate_parsed:
                            features = candidate_features
                            parsed = True
                            break

                    if parsed:
                        results.append((layer.lower(), features))
                        try:
                            self._normalise_result(results, radius)
                        except RuntimeError:
                            continue
                        successful_query = True
                except Exception as exc:
                    query_errors.append(f"{layer}: {exc}")

            if not successful_query:
                detail = "; ".join(query_errors) if query_errors else "no queryable response"
                raise RuntimeError(f"Bhuvan Lightning query unavailable: {detail}")

            return self._normalise_result(results, radius)
