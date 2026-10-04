from datetime import datetime
from pydantic import BaseModel,Field

class WeatherPoint(BaseModel):
    timestamp:datetime
    temperature_c:float|None=None
    humidity_pct:float|None=None
    precipitation_probability_pct:float|None=None
    precipitation_mm:float|None=None
    rain_mm:float|None=None
    showers_mm:float|None=None
    cloud_cover_pct:float|None=None
    cloud_cover_low_pct:float|None=None
    cloud_cover_mid_pct:float|None=None
    cloud_cover_high_pct:float|None=None
    wind_speed_kmh:float|None=None
    wind_direction_deg:float|None=None
    wind_gust_kmh:float|None=None
    weather_code:int|None=None
    weather_icon:int|None=None
    weather_text:str|None=None
    real_feel_temperature_c:float|None=None
    dew_point_c:float|None=None
    visibility_km:float|None=None
    ceiling_m:float|None=None
    uv_index:float|None=None
    pressure_hpa:float|None=None
    precipitation_type:str|None=None
    precipitation_intensity:str|None=None
    thunderstorm_probability_pct:float|None=None
    rain_probability_pct:float|None=None
    solar_irradiance_wm2:float|None=None

class LightningResponse(BaseModel):
    provider:str
    fetched_at:datetime
    interval_minutes:int
    radius_km:float
    strike_count:int=0
    peak_current_a:float|None=None
    flash_rate_per_min:float|None=None
    density_per_km2:float|None=None
    strike_intensity:str|None=None
    latest_observation_time:datetime|None=None
    latest_latitude:float|None=None
    latest_longitude:float|None=None
    warnings:list[str]=Field(default_factory=list)

class WeatherResponse(BaseModel):
    latitude:float
    longitude:float
    provider:str
    fetched_at:datetime
    current:WeatherPoint
    hourly:list[WeatherPoint]=Field(default_factory=list)
    lightning:LightningResponse|None=None
    warnings:list[str]=Field(default_factory=list)

class RadarLayerResponse(BaseModel):
    provider:str
    generated_at:datetime
    tile_template:str
    max_zoom:int
    attribution:str
    warnings:list[str]=Field(default_factory=list)
