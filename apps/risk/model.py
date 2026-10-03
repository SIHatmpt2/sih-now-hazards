"""XGBoost inference with a transparent, non-validated baseline fallback."""
from pathlib import Path
import json,numpy as np
from apps.core.config import get_settings
from apps.core.schemas import FeatureBundle,Hazard,RiskBand
from apps.data_processing.features import FEATURE_NAMES,completeness
class RiskEngine:
    def __init__(self):self.settings=get_settings();self.models={};self.model_features=FEATURE_NAMES.copy();self.calibrated={};self._load_models()
    def _load_models(self):
        p=Path(self.settings.model_manifest_path)
        if not p.exists():return
        try:
            manifest=json.loads(p.read_text(encoding="utf-8"));self.model_features=manifest.get("feature_names",FEATURE_NAMES);import xgboost as xgb;calibrations=manifest.get("calibration") or {}
            for name,artifact in (manifest.get("models") or {}).items():
                a=Path(artifact);a=Path.cwd()/a if not a.is_absolute() else a
                if not a.exists():continue
                m=xgb.XGBClassifier();m.load_model(a.as_posix());hazard=Hazard(name);self.models[hazard]=m;self.calibrated[hazard]=bool((calibrations.get(name) or {}).get("validated",False))
        except Exception:self.models={};self.calibrated={};self.model_features=FEATURE_NAMES.copy()
    def _band(self,s):
        if s<self.settings.risk_threshold_low:return RiskBand.low
        if s<self.settings.risk_threshold_moderate:return RiskBand.moderate
        if s<self.settings.risk_threshold_high:return RiskBand.high
        return RiskBand.very_high
    @staticmethod
    def _norm(v,lo,hi):return 0.0 if v is None else float(np.clip((v-lo)/(hi-lo),0,1))
    def _baseline(self,f,h):
        code=f.weather_code or 0;pp=self._norm(f.precipitation_probability_pct,0,100);cloud=self._norm(f.cloud_cover_pct,0,100);hum=self._norm(f.humidity_pct,45,100);wind=self._norm(f.wind_gust_kmh or f.wind_speed_kmh,0,100);rain=self._norm((f.rain_mm or 0)+(f.showers_mm or 0),0,30);thunder=1.0 if code in (95,96,99) else 0.0;hail=1.0 if code in (96,99) else 0.0;cold=self._norm(18-(f.temperature_c or 18),0,18)
        if h is Hazard.thunderstorm:return float(np.clip(.35*thunder+.20*pp+.15*cloud+.15*hum+.15*wind,0,1))
        if h is Hazard.hailstorm:return float(np.clip(.45*hail+.20*pp+.15*wind+.10*cloud+.10*cold,0,1))
        return float(np.clip(.35*rain+.20*pp+.20*hum+.15*cloud+.10*wind,0,1))
    def _ml_score(self,f,h):
        model=self.models.get(h)
        if model is None:return None
        p=f.model_dump();row=[p.get(n) for n in self.model_features]
        if any(v is None for v in row):return None
        return float(np.clip(model.predict_proba(np.asarray([row],dtype=float))[0,1],0,1))
    def score(self,f,h):
        ml=self._ml_score(f,h);score=ml if ml is not None else self._baseline(f,h);stype="calibrated_probability" if ml is not None and self.calibrated.get(h,False) else "model_score";version=self.settings.model_version if ml is not None else "baseline-v1";unc=float(np.clip(.05+.35*(1-completeness(f)),0,1));warnings=[] if ml is not None else ["Baseline scoring is not scientifically validated and must not be treated as an official warning.","Lightning observations and cloud-top retrievals may be unavailable from the default provider."]
        if ml is not None and not self.calibrated.get(h,False):warnings.append("Model output is not calibration-validated; it is reported as a model score.")
        if unc>.20:warnings.append("Prediction uncertainty is elevated because the feature bundle is incomplete.")
        return {"hazard":h,"score":score,"score_type":stype,"risk_band":self._band(score),"model_version":version,"uncertainty":unc,"input_timestamp":f.observed_at,"warnings":warnings}
