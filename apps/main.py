"""SkyIntel FastAPI entry point.

Backend integration is intentionally scaffolded here. Domain logic for weather
providers, data processing, risk inference, and persistence will be added in
their dedicated modules without changing the frontend UI.
"""
from fastapi import FastAPI

app = FastAPI(title="SkyIntel", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}