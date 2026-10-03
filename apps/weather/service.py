from datetime import UTC
from apps.core.cache import RedisCache
from apps.core.config import get_settings
from apps.core.schemas import FeatureBundle
from apps.weather.open_meteo import OpenMeteoProvider
from apps.weather.schemas import WeatherPoint,WeatherResponse
class WeatherService:
    def __init__(self):self.settings=get_settings();self.provider=OpenMeteoProvider();self.cache=RedisCache()
    async def get(self,latitude,longitude,hours=6):
        key=f"weather:{latitude:.4f}:{longitude:.4f}:{hours}";cached=await self.cache.get_json(key)
        if cached:return WeatherResponse.model_validate(cached)
        if self.settings.weather_provider!="open-meteo":raise RuntimeError(f"Unsupported weather provider: {self.settings.weather_provider}")
        result=await self.provider.fetch(latitude,longitude,hours);await self.cache.set_json(key,result.model_dump(mode="json"),self.settings.weather_cache_ttl_seconds);return result
def cloud_type_from_weather(p:WeatherPoint):
    if p.weather_code in (95,96,99):return "Deep Convective"
    c=p.cloud_cover_pct or 0
    if c>=85:return "Deep Cloud Layer"
    if c>=60:return "Multi-layer Cloud"
    if c>=30:return "Broken Cloud"
    return "Partly Cloudy"
def point_to_features(p:WeatherPoint,latitude,longitude):
    ts=p.timestamp if p.timestamp.tzinfo else p.timestamp.replace(tzinfo=UTC)
    return FeatureBundle(latitude=latitude,longitude=longitude,observed_at=ts,temperature_c=p.temperature_c,humidity_pct=p.humidity_pct,precipitation_probability_pct=p.precipitation_probability_pct,precipitation_mm=p.precipitation_mm,rain_mm=p.rain_mm,showers_mm=p.showers_mm,cloud_cover_pct=p.cloud_cover_pct,wind_speed_kmh=p.wind_speed_kmh,wind_direction_deg=p.wind_direction_deg,wind_gust_kmh=p.wind_gust_kmh,weather_code=p.weather_code,cloud_direction_deg=p.wind_direction_deg,cloud_velocity_kmh=p.wind_speed_kmh,cloud_type=cloud_type_from_weather(p),downburst_velocity_kmh=p.wind_gust_kmh,monsoon_status="Active" if ts.month in (6,7,8,9) else "Off-season")
