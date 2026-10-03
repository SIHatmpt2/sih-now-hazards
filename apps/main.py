"""SkyIntel FastAPI application wiring."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apps.core.config import get_settings
from apps.core.logging import configure_logging
from apps.core.router import router as core_router
from apps.risk.router import router as risk_router
from apps.weather.router import router as weather_router
settings=get_settings();configure_logging(settings.log_level);BASE_DIR=Path(__file__).resolve().parent.parent;TEMPLATES_DIR=BASE_DIR/"templates";STATIC_DIR=BASE_DIR/"static"
app=FastAPI(title=settings.app_name,version="1.0.0",docs_url="/docs",redoc_url="/redoc");app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"]);app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static");app.include_router(core_router,prefix="/api/v1");app.include_router(weather_router,prefix="/api/v1");app.include_router(risk_router,prefix="/api/v1")
@app.get("/",include_in_schema=False)
def landing_page():return FileResponse(TEMPLATES_DIR/"index.html")
@app.get("/dashboard",include_in_schema=False)
def dashboard_page():return FileResponse(TEMPLATES_DIR/"dashboard.html")

@app.get("/dashboard.html",include_in_schema=False)
def legacy_dashboard_page():return dashboard_page()
@app.get("/health",include_in_schema=False)
def health():return {"status":"ok","service":settings.app_name,"version":app.version}
