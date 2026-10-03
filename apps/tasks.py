"""Celery worker and beat schedule."""
import asyncio
from celery import Celery
from apps.core.config import get_settings
from apps.core.db import SessionLocal
from apps.core.locations import DEFAULT_LOCATIONS
from apps.data_processing.ingestion import ingest_location
s=get_settings();celery_app=Celery("skyintel",broker=s.celery_broker_url,backend=s.celery_result_backend);celery_app.conf.update(task_serializer="json",result_serializer="json",accept_content=["json"],timezone="UTC",enable_utc=True,task_acks_late=True,worker_prefetch_multiplier=1,task_track_started=True,beat_schedule={"poll-default-locations":{"task":"apps.tasks.enqueue_default_ingestion","schedule":600.0}})
@celery_app.task(bind=True,autoretry_for=(Exception,),retry_backoff=True,retry_kwargs={"max_retries":3})
def ingest_location_task(self,location):
    db=SessionLocal()
    try:return asyncio.run(ingest_location(db,**location))
    finally:db.close()
@celery_app.task
def enqueue_default_ingestion():return [ingest_location_task.delay(x).id for x in DEFAULT_LOCATIONS]
