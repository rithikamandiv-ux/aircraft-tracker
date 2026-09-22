import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.opensky_client import OpenSkyClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared resources on startup, release them on shutdown."""
    settings = get_settings()

    http = httpx.AsyncClient(timeout=settings.http_timeout_s)
    app.state.opensky = OpenSkyClient(
        client_id=settings.opensky_client_id,
        client_secret=settings.opensky_client_secret,
        http=http,
    )

    logger.info("Startup complete. Watching region %s", settings.region.model_dump())
    yield

    await http.aclose()
    logger.info("Shutdown complete.")


settings = get_settings()

app = FastAPI(
    title="Aircraft Tracker API",
    description="Live aircraft positions over Sri Lankan airspace, sourced from OpenSky.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "connected_clients": 0,   # wired up in Step 2.2
        "poller_running": False,  # wired up in Step 2.3
        "last_fetch_at": None,    # wired up in Step 2.3
    }