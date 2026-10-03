"""Train XGBoost with chronological holdout."""
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from sklearn.metrics import precision_score,recall_score,roc_auc_score
from xgboost import XGBClassifier
from apps.data_processing.features import FEATURE_NAMES
def train(input_path,target,output,time_col="observed_at"):
    p=Path(input_path);df=pd.read_parquet(p) if p.suffix.lower()==".parquet" else pd.read_csv(p);missing=[x for x in [target,time_col,*FEATURE_NAMES] if x not in df.columns]
    if missing:raise ValueError(f"Missing required columns: {missing}")
    df=df.dropna(subset=[target,time_col]).sort_values(time_col).reset_index(drop=True)
    if len(df)<10 or df[target].nunique()<2:raise ValueError("Training data must contain at least 10 rows and both target classes")
    cut=min(len(df)-1,max(1,int(len(df)*.8)));tr,te=df.iloc[:cut],df.iloc[cut:];xtr=tr[FEATURE_NAMES].apply(pd.to_numeric,errors="coerce").fillna(0);xte=te[FEATURE_NAMES].apply(pd.to_numeric,errors="coerce").fillna(0);ytr=tr[target].astype(int);yte=te[target].astype(int)
    if ytr.nunique()<2:raise ValueError("Chronological training split contains only one target class; use more historical data")
    model=XGBClassifier(n_estimators=300,max_depth=5,learning_rate=.05,subsample=.8,colsample_bytree=.8,objective="binary:logistic",eval_metric="logloss",random_state=42);model.fit(xtr,ytr);prob=model.predict_proba(xte)[:,1];pred=(prob>=.5).astype(int);metrics={"precision":float(precision_score(yte,pred,zero_division=0)),"recall":float(recall_score(yte,pred,zero_division=0)),"roc_auc":float(roc_auc_score(yte,prob)) if yte.nunique()>1 else None}
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True);model.save_model(out.as_posix());manifest={"version":out.stem,"score_type":"model_score","feature_names":FEATURE_NAMES,"models":{target:out.as_posix()},"metrics":metrics,"training_period":{"start":str(df[time_col].min()),"end":str(df[time_col].max())},"calibration":{target:{"validated":False}},"artifact_sha256":hashlib.sha256(out.read_bytes()).hexdigest()};(out.parent/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8");return manifest
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--input",required=True);ap.add_argument("--target",required=True);ap.add_argument("--output",required=True);ap.add_argument("--time-col",default="observed_at");a=ap.parse_args();print(json.dumps(train(a.input,a.target,a.output,a.time_col),indent=2))
