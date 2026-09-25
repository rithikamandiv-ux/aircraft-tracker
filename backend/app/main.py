import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import (
    APIRouter,
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.connection_manager import ConnectionManager
from app.opensky_client import OpenSkyClient
from app.poller import Poller

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    state = request.app.state
    latest = state.poller.latest
    return {
        "status": "ok",
        "connected_clients": state.manager.client_count,
        "poller_running": state.poller.is_running,
        "last_fetch_at": latest.fetched_at if latest else None,
        "aircraft_count": len(latest.aircraft) if latest else 0,
        "stale": latest.stale if latest else None,
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    state = websocket.app.state

    origin = websocket.headers.get("origin")
    if origin is not None and origin not in state.settings.allowed_origins:
        logger.warning("Rejected WebSocket from origin: %s", origin)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    manager: ConnectionManager = state.manager
    poller: Poller = state.poller

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


def create_app(
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Build the application.

    Production calls this with no arguments. Tests pass their own settings
    and a fake HTTP transport, so no real credentials or network are needed.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
    )
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Build in dependency order: HTTP client -> OpenSky client -> manager -> poller
        http = httpx.AsyncClient(timeout=settings.http_timeout_s, transport=transport)
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
        logger.info(
            "Startup complete. Watching region %s", settings.region.model_dump()
        )

        yield

        # Tear down in reverse: stop polling before closing the connection it uses
        await app.state.poller.close()
        await http.aclose()
        logger.info("Shutdown complete.")

    app = FastAPI(
        title="Aircraft Tracker API",
        description="Live aircraft positions over South Asian airspace, from OpenSky.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
