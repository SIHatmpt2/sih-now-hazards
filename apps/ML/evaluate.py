"""Evaluate an XGBoost artifact."""
import argparse,json
from pathlib import Path
import pandas as pd
from sklearn.metrics import precision_score,recall_score,confusion_matrix
from xgboost import XGBClassifier
from apps.data_processing.features import FEATURE_NAMES
def evaluate(input_path,target,model_path):
    p=Path(input_path);df=pd.read_parquet(p) if p.suffix.lower()==".parquet" else pd.read_csv(p);missing=[x for x in [target,*FEATURE_NAMES] if x not in df.columns]
    if missing:raise ValueError(f"Missing required columns: {missing}")
    df=df.dropna(subset=[target]);x=df[FEATURE_NAMES].apply(pd.to_numeric,errors="coerce").fillna(0);y=df[target].astype(int);m=XGBClassifier();m.load_model(model_path);prob=m.predict_proba(x)[:,1];pred=(prob>=.5).astype(int);tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel();return {"precision":float(precision_score(y,pred,zero_division=0)),"recall":float(recall_score(y,pred,zero_division=0)),"false_alarm_rate":float(fp/(fp+tn)) if fp+tn else 0.0,"confusion_matrix":{"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp)}}
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--input",required=True);ap.add_argument("--target",required=True);ap.add_argument("--model",required=True);a=ap.parse_args();print(json.dumps(evaluate(a.input,a.target,a.model),indent=2))
