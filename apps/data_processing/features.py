FEATURE_NAMES=["temperature_c","humidity_pct","precipitation_probability_pct","precipitation_mm","rain_mm","showers_mm","cloud_cover_pct","wind_speed_kmh","wind_gust_kmh","weather_code","lightning_flash_rate_per_min","lightning_density_per_km2","cloud_velocity_kmh","downburst_velocity_kmh"]
from apps.data_processing.quality import quality_warnings
def feature_vector(f):return [f.model_dump().get(x) for x in FEATURE_NAMES],quality_warnings(f)
def completeness(f):v,_=feature_vector(f);return sum(x is not None for x in v)/len(v)
