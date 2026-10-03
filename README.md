# SkyIntel — Convective Scale Nowcasting Backend

Backend implementation follows the supplied SkyIntel architecture and leaves the existing frontend files untouched.

Implemented: FastAPI and API versioning; PostgreSQL/PostGIS schema and Alembic migration; IMD and AccuWeather weather adapters; Open-Meteo development fallback; RainViewer radar metadata; Redis cache; MinIO raw payload storage; QA/freshness checks; feature contract; XGBoost artifact loading; transparent baseline scoring; six-hour risk nowcast; Celery worker and Beat; training/evaluation utilities; tests.

The weather service uses IMD as the primary configured source and AccuWeather as the secondary configured source. It falls back to Open-Meteo only when neither keyed source is configured. Trained/scientifically validated models and complete satellite/3D rendering are not supplied by the architecture, so unvalidated outputs are explicitly reported as model_score.

## Docker

Copy .env.example to .env, replace placeholder secrets, then run:

docker compose up --build

Open http://localhost:8001/ and http://localhost:8001/docs. MinIO console: http://localhost:9002.

## Local API

For local API processes, use localhost ports for DATABASE_URL, Redis URLs and S3_ENDPOINT_URL in .env. Then run:

docker compose up -d postgres redis minio
alembic upgrade head
uvicorn apps.main:app --reload --host 127.0.0.1 --port 8001

## Routes

GET /health
GET /api/v1/ready
GET /api/v1/locations/search?q=shimla
GET /api/v1/weather/current?latitude=31.10&longitude=77.17
GET /api/v1/weather/forecast?latitude=31.10&longitude=77.17&hours=6
GET /api/v1/weather/layers
POST /api/v1/risk/score
GET /api/v1/risk/nowcast?latitude=31.10&longitude=77.17&hours=6
