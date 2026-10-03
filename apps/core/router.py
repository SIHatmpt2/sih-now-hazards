from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from apps.core.cache import RedisCache
from apps.core.db import check_database,get_db
from apps.core.locations import find_locations,seed_default_locations
from apps.core.schemas import LocationOut,ReadinessResponse
from apps.core.storage import ObjectStorage
router=APIRouter(tags=["core"])
@router.get("/locations/search",response_model=list[LocationOut])
def search_locations(q:str|None=Query(None,max_length=100),db:Session=Depends(get_db)):
    seed_default_locations(db);return [LocationOut(slug=x.slug,name=x.name,state=x.state,latitude=x.latitude,longitude=x.longitude) for x in find_locations(db,q)]
@router.get("/ready",response_model=ReadinessResponse)
async def ready():
    c={"database":check_database(),"redis":await RedisCache().ping(),"object_storage":ObjectStorage().healthcheck()};return ReadinessResponse(status="ready" if all(c.values()) else "degraded",components=c)
