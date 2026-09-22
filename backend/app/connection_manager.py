import asyncio
import logging

from fastapi import WebSocket

from app.models import SnapshotMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Tracks connected WebSocket clients and broadcasts messages to them."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    @property
    def client_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("Client connected (total: %d)", self.client_count)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("Client disconnected (total: %d)", self.client_count)

    async def send_to(self, websocket: WebSocket, message: SnapshotMessage) -> None:
        await websocket.send_text(message.model_dump_json())

    async def broadcast(self, message: SnapshotMessage) -> None:
        if not self._connections:
            return

        payload = message.model_dump_json()

        # Iterate over a copy: a client may disconnect mid-broadcast
        results = await asyncio.gather(
            *(ws.send_text(payload) for ws in list(self._connections)),
            return_exceptions=True,
        )

        for websocket, result in zip(list(self._connections), results):
            if isinstance(result, Exception):
                logger.warning("Dropping client after send failure: %s", result)
                self._connections.discard(websocket)