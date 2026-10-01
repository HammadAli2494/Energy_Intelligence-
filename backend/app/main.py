import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.anomalies import router as anomalies_router
from app.api.routes.contact import router as contact_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.forecast import router as forecast_router
from app.api.routes.health import router as health_router
from app.api.routes.weather import router as weather_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.mongodb import close_mongo_connection, connect_to_mongo, get_database
from app.services.app_data import app_data
from app.services.persistence import seed_analytics_store

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting Energy Intelligence API.")
    connect_to_mongo()
    app_data.load()
    if get_database() is not None and app_data.ready:
        seed_analytics_store(app_data)
    yield
    close_mongo_connection()
    logger.info("Shutting down Energy Intelligence API.")


app = FastAPI(
    title="Energy Intelligence API",
    description="Backend for the Energy Demand Forecasting & Anomaly Detection platform.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(weather_router, prefix="/api/v1")
app.include_router(forecast_router, prefix="/api/v1")
app.include_router(anomalies_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(contact_router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error: %s", exc.__class__.__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )
