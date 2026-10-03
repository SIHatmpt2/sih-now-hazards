"""Risk orchestration and persistence."""
from datetime import UTC,datetime
from apps.core.locations import get_or_create_location
from apps.core.models import Prediction
from apps.core.schemas import Hazard,RiskResultItem,RiskScoreResponse
from apps.data_processing.quality import validate_freshness,quality_warnings
from apps.risk.model import RiskEngine
from apps.weather.service import WeatherService,point_to_features
class RiskService:
    def __init__(self):self.engine=RiskEngine();self.weather=WeatherService()
    async def build_features(self,lat,lon):return point_to_features((await self.weather.get(lat,lon,1)).current,lat,lon)
    async def score(self,lat,lon,horizon,features=None):
        f=features or await self.build_features(lat,lon)
        if abs(f.latitude-lat)>.001 or abs(f.longitude-lon)>.001:raise ValueError("Feature coordinates do not match request coordinates")
        fresh,msg=validate_freshness(f.observed_at)
        if not fresh:raise ValueError(msg or "Input data is stale")
        warnings=quality_warnings(f);results=[RiskResultItem(**self.engine.score(f,h),forecast_horizon_hours=horizon) for h in Hazard]
        for r in results:warnings.extend(r.warnings)
        return RiskScoreResponse(latitude=lat,longitude=lon,issued_at=datetime.now(UTC),data_source="open-meteo" if features is None else "provided-feature-bundle",results=results,warnings=list(dict.fromkeys(warnings)))
    def persist(self,db,response,features):
        slug=f"coord-{response.latitude:.4f}-{response.longitude:.4f}".replace(".","_").replace("-","m");loc=get_or_create_location(db,slug,f"{response.latitude:.4f}, {response.longitude:.4f}",None,response.latitude,response.longitude)
        for r in response.results:db.add(Prediction(location_id=loc.id,hazard=r.hazard.value,score=r.score,score_type=r.score_type,risk_band=r.risk_band.value,forecast_hour=r.forecast_horizon_hours,issued_at=response.issued_at,valid_at=features.observed_at,model_version=r.model_version,uncertainty=r.uncertainty,feature_snapshot=features.model_dump(mode="json"),warnings=r.warnings))
        db.commit()
async def six_hour_nowcast(lat,lon,hours):
    s=RiskService();weather=await s.weather.get(lat,lon,hours);out=[]
    for i,p in enumerate(weather.hourly,1):
        f=point_to_features(p,lat,lon);rs=[RiskResultItem(**s.engine.score(f,h),forecast_horizon_hours=i) for h in Hazard];out.append(RiskScoreResponse(latitude=lat,longitude=lon,issued_at=weather.fetched_at,data_source=weather.provider,results=rs,warnings=list(dict.fromkeys([w for r in rs for w in r.warnings]))))
    return out
