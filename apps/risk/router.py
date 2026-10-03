"""Risk scoring routes."""
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from apps.core.config import get_settings
from apps.core.db import get_db
from apps.core.schemas import RiskScoreRequest,RiskScoreResponse
from apps.risk.service import RiskService,six_hour_nowcast
router=APIRouter(prefix="/risk",tags=["risk"]);service=RiskService()
@router.post("/score",response_model=RiskScoreResponse)
async def score_risk(request:RiskScoreRequest,db:Session=Depends(get_db)):
    try:
        response=await service.score(request.latitude,request.longitude,request.forecast_horizon_hours,request.features)
        if get_settings().persist_predictions:
            try:service.persist(db,response,request.features or await service.build_features(request.latitude,request.longitude))
            except Exception:db.rollback();response.warnings.append("Prediction persistence is temporarily unavailable; score generation completed.")
        return response
    except ValueError as exc:raise HTTPException(422,detail=str(exc)) from exc
    except Exception as exc:raise HTTPException(502,detail=f"Risk pipeline failed: {exc}") from exc
@router.get("/nowcast",response_model=list[RiskScoreResponse])
async def nowcast(latitude:float=Query(...,ge=-90,le=90),longitude:float=Query(...,ge=-180,le=180),hours:int=Query(6,ge=1,le=6)):
    try:return await six_hour_nowcast(latitude,longitude,hours)
    except Exception as exc:raise HTTPException(502,detail=f"Nowcast pipeline failed: {exc}") from exc
