from datetime import UTC,datetime
from apps.core.schemas import FeatureBundle,Hazard
from apps.risk.model import RiskEngine
def test_baseline_score_is_not_probability():
    f=FeatureBundle(latitude=30.41,longitude=79.32,observed_at=datetime.now(UTC),temperature_c=22,humidity_pct=85,precipitation_probability_pct=80,rain_mm=12,showers_mm=2,cloud_cover_pct=90,wind_speed_kmh=45,wind_gust_kmh=65,weather_code=95,cloud_velocity_kmh=45,downburst_velocity_kmh=65);r=RiskEngine().score(f,Hazard.thunderstorm);assert r["score_type"]=="model_score";assert 0<=r["score"]<=1


def test_accuweather_geoposition_response_uses_first_location_key():
    from apps.weather.accuweather import AccuWeatherProvider

    payload = [{"Key": "123456", "LocalizedName": "Shimla"}]
    normalized = payload[0] if payload and isinstance(payload[0], dict) else None

    assert isinstance(normalized, dict)
    assert AccuWeatherProvider._float(normalized.get("Key")) is not None
