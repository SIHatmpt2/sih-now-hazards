from datetime import UTC,datetime,timedelta
from apps.core.config import get_settings
def missing_feature_names(f):return [n for n,v in f.model_dump().items() if n not in {"latitude","longitude","observed_at"} and v is None]
def validate_freshness(ts,max_age_minutes=None):
    limit=max_age_minutes or get_settings().max_weather_age_minutes;d=ts if ts.tzinfo else ts.replace(tzinfo=UTC);age=datetime.now(UTC)-d
    if age<timedelta(minutes=-5):return False,"Input timestamp is in the future"
    if age>timedelta(minutes=limit):return False,f"Input data is stale ({age.total_seconds()/60:.1f} minutes old)"
    return True,None
def quality_warnings(f):
    w=[];m=missing_feature_names(f)
    if m:w.append("Missing optional features: "+", ".join(m))
    ok,msg=validate_freshness(f.observed_at)
    if not ok and msg:w.append(msg)
    return w
