from datetime import datetime
from pydantic import BaseModel,Field
class WeatherPoint(BaseModel):timestamp:datetime;temperature_c:float|None=None;humidity_pct:float|None=None;precipitation_probability_pct:float|None=None;precipitation_mm:float|None=None;rain_mm:float|None=None;showers_mm:float|None=None;cloud_cover_pct:float|None=None;cloud_cover_low_pct:float|None=None;cloud_cover_mid_pct:float|None=None;cloud_cover_high_pct:float|None=None;wind_speed_kmh:float|None=None;wind_direction_deg:float|None=None;wind_gust_kmh:float|None=None;weather_code:int|None=None
class WeatherResponse(BaseModel):latitude:float;longitude:float;provider:str;fetched_at:datetime;current:WeatherPoint;hourly:list[WeatherPoint]=Field(default_factory=list);warnings:list[str]=Field(default_factory=list)
class RadarLayerResponse(BaseModel):provider:str;generated_at:datetime;tile_template:str;max_zoom:int;attribution:str;warnings:list[str]=Field(default_factory=list)
