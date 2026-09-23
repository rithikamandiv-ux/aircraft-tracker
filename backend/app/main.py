import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.connection_manager import ConnectionManager
from app.opensky_client import OpenSkyClient
from app.poller import Poller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared resources on startup, release them on shutdown."""
    settings = get_settings()

    # Build in dependency order: HTTP client -> OpenSky client -> manager -> poller
    http = httpx.AsyncClient(timeout=settings.http_timeout_s)

    app.state.opensky = OpenSkyClient(
        client_id=settings.opensky_client_id,
        client_secret=settings.opensky_client_secret,
        http=http,
    )
    app.state.manager = ConnectionManager()
    app.state.poller = Poller(
        client=app.state.opensky,
        manager=app.state.manager,
        settings=settings,
    )

    logger.info("Startup complete. Watching region %s", settings.region.model_dump())

    yield  # ---- the application runs here ----

    # Shutdown: stop the poller first, then close the connection it uses
    await app.state.poller.stop()
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
    poller: Poller = app.state.poller
    latest = poller.latest
    return {
        "status": "ok",
        "connected_clients": app.state.manager.client_count,
        "poller_running": poller.is_running,
        "last_fetch_at": latest.fetched_at if latest else None,
        "aircraft_count": len(latest.aircraft) if latest else 0,
        "stale": latest.stale if latest else None,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in settings.allowed_origins:
        logger.warning("Rejected WebSocket from origin: %s", origin)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    manager: ConnectionManager = websocket.app.state.manager
    poller: Poller = websocket.app.state.poller

    await manager.connect(websocket)
    poller.ensure_running()

    try:
        # Send cached data immediately so the map is not blank while waiting
        if poller.latest is not None:
            await manager.send_to(websocket, poller.latest)

        # Keep the connection open and detect disconnects
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        poller.schedule_stop()
    except Exception:
        logger.exception("Unexpected WebSocket error")
        manager.disconnect(websocket)
        poller.schedule_stop()
