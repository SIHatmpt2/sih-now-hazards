"""Weather ingestion: fetch -> QA -> MinIO -> PostGIS."""
from datetime import UTC,datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from apps.core.config import get_settings
from apps.core.locations import get_or_create_location
from apps.core.models import IngestionRun,WeatherObservation
from apps.core.storage import ObjectStorage
from apps.data_processing.quality import validate_freshness
from apps.weather.service import WeatherService
async def ingest_location(db:Session,slug,name,state,latitude,longitude):
    s=get_settings();run=IngestionRun(provider=s.weather_provider,status="started",started_at=datetime.now(UTC),location_slug=slug);db.add(run);db.commit();db.refresh(run)
    try:
        weather=await WeatherService().get(latitude,longitude,6);loc=get_or_create_location(db,slug,name,state,latitude,longitude);key=None
        if s.enable_raw_object_storage:
            key=f"raw/weather/{weather.provider}/{datetime.now(UTC):%Y/%m/%d}/{slug}/{datetime.now(UTC):%Y%m%dT%H%M%SZ}.json";ObjectStorage().put_json(key,weather.model_dump(mode="json"))
        count=0
        for p in [weather.current,*weather.hourly]:
            existing=db.scalar(select(WeatherObservation).where(WeatherObservation.location_id==loc.id,WeatherObservation.provider==weather.provider,WeatherObservation.observed_at==p.timestamp));ok,msg=validate_freshness(p.timestamp,1440);values={"temperature_c":p.temperature_c,"humidity_pct":p.humidity_pct,"precipitation_probability_pct":p.precipitation_probability_pct,"precipitation_mm":p.precipitation_mm,"rain_mm":p.rain_mm,"showers_mm":p.showers_mm,"cloud_cover_pct":p.cloud_cover_pct,"cloud_cover_low_pct":p.cloud_cover_low_pct,"cloud_cover_mid_pct":p.cloud_cover_mid_pct,"cloud_cover_high_pct":p.cloud_cover_high_pct,"wind_speed_kmh":p.wind_speed_kmh,"wind_direction_deg":p.wind_direction_deg,"wind_gust_kmh":p.wind_gust_kmh,"weather_code":p.weather_code,"quality_flags":[] if ok else [msg or "stale"],"raw_object_key":key,"payload":p.model_dump(mode="json")}
            if existing:
                for k,v in values.items():setattr(existing,k,v)
            else:db.add(WeatherObservation(location_id=loc.id,provider=weather.provider,observed_at=p.timestamp,**values))
            count+=1
        run.status="success";run.finished_at=datetime.now(UTC);run.records_written=count;run.raw_object_key=key;run.metadata_json={"latitude":latitude,"longitude":longitude,"hourly_points":len(weather.hourly)};db.commit();return count
    except Exception as exc:
        db.rollback();run=db.get(IngestionRun,run.id)
        if run:run.status="failed";run.finished_at=datetime.now(UTC);run.error=str(exc);db.commit()
        raise
