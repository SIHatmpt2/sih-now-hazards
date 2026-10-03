from datetime import datetime
from enum import Enum
from pydantic import BaseModel,Field,ConfigDict,field_validator
class Hazard(str,Enum):thunderstorm="thunderstorm";hailstorm="hailstorm";cloudburst="cloudburst"
class RiskBand(str,Enum):low="Low";moderate="Moderate";high="High";very_high="Very High"
class FeatureBundle(BaseModel):
    model_config=ConfigDict(extra="forbid");latitude:float=Field(ge=-90,le=90);longitude:float=Field(ge=-180,le=180);observed_at:datetime;temperature_c:float|None=Field(None,ge=-80,le=70);humidity_pct:float|None=Field(None,ge=0,le=100);precipitation_probability_pct:float|None=Field(None,ge=0,le=100);precipitation_mm:float|None=Field(None,ge=0);rain_mm:float|None=Field(None,ge=0);showers_mm:float|None=Field(None,ge=0);cloud_cover_pct:float|None=Field(None,ge=0,le=100);wind_speed_kmh:float|None=Field(None,ge=0);wind_direction_deg:float|None=Field(None,ge=0,le=360);wind_gust_kmh:float|None=Field(None,ge=0);weather_code:int|None=Field(None,ge=0,le=99);lightning_flash_rate_per_min:float|None=Field(None,ge=0);lightning_density_per_km2:float|None=Field(None,ge=0);lightning_strike_intensity:float|None=Field(None,ge=0);cloud_direction_deg:float|None=Field(None,ge=0,le=360);cloud_velocity_kmh:float|None=Field(None,ge=0);cloud_type:str|None=None;downburst_velocity_kmh:float|None=Field(None,ge=0);monsoon_status:str|None=None
    @field_validator("observed_at")
    @classmethod
    def tz_required(cls,v):
        if v.tzinfo is None:raise ValueError("observed_at must include a timezone")
        return v
class RiskScoreRequest(BaseModel):latitude:float=Field(ge=-90,le=90);longitude:float=Field(ge=-180,le=180);forecast_horizon_hours:int=Field(6,ge=1,le=6);features:FeatureBundle|None=None
class RiskResultItem(BaseModel):hazard:Hazard;score:float=Field(ge=0,le=1);score_type:str;risk_band:RiskBand;model_version:str;uncertainty:float|None=Field(None,ge=0,le=1);input_timestamp:datetime;forecast_horizon_hours:int;warnings:list[str]=Field(default_factory=list)
class RiskScoreResponse(BaseModel):latitude:float;longitude:float;issued_at:datetime;data_source:str;results:list[RiskResultItem];warnings:list[str]=Field(default_factory=list)
class LocationOut(BaseModel):slug:str;name:str;state:str|None=None;latitude:float;longitude:float
class ReadinessResponse(BaseModel):status:str;components:dict[str,bool]
