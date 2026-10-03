from fastapi import APIRouter,HTTPException,Query
from apps.weather.radar import get_latest_radar_layer
from apps.weather.schemas import RadarLayerResponse,WeatherResponse
from apps.weather.service import WeatherService
router=APIRouter(prefix="/weather",tags=["weather"]);service=WeatherService()
@router.get("/current",response_model=WeatherResponse)
async def current_weather(latitude:float=Query(...,ge=-90,le=90),longitude:float=Query(...,ge=-180,le=180)):
    try:return await service.get(latitude,longitude,6)
    except Exception as exc:raise HTTPException(502,detail=f"Weather provider unavailable: {exc}") from exc
@router.get("/forecast",response_model=WeatherResponse)
async def forecast_weather(latitude:float=Query(...,ge=-90,le=90),longitude:float=Query(...,ge=-180,le=180),hours:int=Query(6,ge=1,le=6)):
    try:return await service.get(latitude,longitude,hours)
    except Exception as exc:raise HTTPException(502,detail=f"Weather provider unavailable: {exc}") from exc
@router.get("/layers",response_model=RadarLayerResponse)
async def weather_layers():
    try:return await get_latest_radar_layer()
    except Exception as exc:raise HTTPException(502,detail=f"Radar provider unavailable: {exc}") from exc
