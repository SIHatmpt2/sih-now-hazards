from datetime import UTC,datetime
import httpx
from apps.weather.schemas import RadarLayerResponse
RAINVIEWER_INDEX="https://api.rainviewer.com/public/weather-maps.json"
async def get_latest_radar_layer():
    async with httpx.AsyncClient(timeout=12) as client:r=await client.get(RAINVIEWER_INDEX,headers={"User-Agent":"SkyIntel/1.0"})
    r.raise_for_status();data=r.json();frames=((data.get("radar") or {}).get("past") or [])
    if not frames or not data.get("host"):raise RuntimeError("No radar frame is currently available")
    f=frames[-1];return RadarLayerResponse(provider="RainViewer",generated_at=datetime.fromtimestamp(f["time"],tz=UTC),tile_template=f'{data["host"]}{f["path"]}/256/{{z}}/{{x}}/{{y}}/2/1_1.png',max_zoom=7,attribution="Weather data © RainViewer")
