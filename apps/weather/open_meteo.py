from datetime import UTC,datetime
import httpx
from apps.core.config import get_settings
from apps.weather.schemas import WeatherPoint,WeatherResponse
class OpenMeteoProvider:
    name="open-meteo"
    def __init__(self):self.settings=get_settings()
    @staticmethod
    def _ts(v):
        d=datetime.fromisoformat(v.replace("Z","+00:00"));return d if d.tzinfo else d.replace(tzinfo=UTC)
    @classmethod
    def _point(cls,h,i):
        def g(k):a=h.get(k) or [];return a[i] if i<len(a) else None
        return WeatherPoint(timestamp=cls._ts(g("time")),temperature_c=g("temperature_2m"),humidity_pct=g("relative_humidity_2m"),precipitation_probability_pct=g("precipitation_probability"),precipitation_mm=g("precipitation"),rain_mm=g("rain"),showers_mm=g("showers"),cloud_cover_pct=g("cloud_cover"),cloud_cover_low_pct=g("cloud_cover_low"),cloud_cover_mid_pct=g("cloud_cover_mid"),cloud_cover_high_pct=g("cloud_cover_high"),wind_speed_kmh=g("wind_speed_10m"),wind_direction_deg=g("wind_direction_10m"),wind_gust_kmh=g("wind_gusts_10m"),weather_code=g("weather_code"))
    async def fetch(self,latitude,longitude,hours=6):
        params={"latitude":latitude,"longitude":longitude,"current":"temperature_2m,relative_humidity_2m,precipitation,rain,showers,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m","hourly":"temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,rain,showers,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,wind_direction_10m,wind_gusts_10m,weather_code","forecast_hours":max(hours,7),"timezone":"UTC","wind_speed_unit":"kmh","precipitation_unit":"mm","temperature_unit":"celsius"}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            r=await client.get(self.settings.weather_api_base_url,params=params,headers={"User-Agent":"SkyIntel/1.0"});r.raise_for_status();data=r.json()
        h=data.get("hourly") or {};points=[self._point(h,i) for i in range(min(hours,len(h.get("time",[]))))];cur=data.get("current") or {}
        current=WeatherPoint(timestamp=self._ts(cur["time"]),temperature_c=cur.get("temperature_2m"),humidity_pct=cur.get("relative_humidity_2m"),precipitation_mm=cur.get("precipitation"),rain_mm=cur.get("rain"),showers_mm=cur.get("showers"),cloud_cover_pct=cur.get("cloud_cover"),wind_speed_kmh=cur.get("wind_speed_10m"),wind_direction_deg=cur.get("wind_direction_10m"),wind_gust_kmh=cur.get("wind_gusts_10m"),weather_code=cur.get("weather_code"))
        return WeatherResponse(latitude=float(data.get("latitude",latitude)),longitude=float(data.get("longitude",longitude)),provider=self.name,fetched_at=datetime.now(UTC),current=current,hourly=points)
