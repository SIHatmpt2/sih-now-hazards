"""Celery application scaffold for asynchronous SkyIntel jobs."""
import os
from celery import Celery

celery_app = Celery(
    "skyintel",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
)