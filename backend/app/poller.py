import asyncio
import logging
import time

from app.config import Settings
from app.connection_manager import ConnectionManager
from app.models import SnapshotMessage
from app.opensky_client import OpenSkyClient

logger = logging.getLogger(__name__)


class Poller:
    """Polls OpenSky on an interval, but only while clients are connected."""

    def __init__(
        self,
        client: OpenSkyClient,
        manager: ConnectionManager,
        settings: Settings,
    ) -> None:
        self._client = client
        self._manager = manager
        self._settings = settings

        self._task: asyncio.Task | None = None
        self._stop_timer: asyncio.Task | None = None
        self._latest: SnapshotMessage | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def latest(self) -> SnapshotMessage | None:
        return self._latest

    def ensure_running(self) -> None:
        """Called when a client connects."""
        # A client returned during the grace period: cancel the pending stop
        if self._stop_timer is not None:
            self._stop_timer.cancel()
            self._stop_timer = None
            logger.info("Client returned during grace period; poller stays alive")

        if self.is_running:
            return

        self._task = asyncio.create_task(self._run())
        logger.info("Poller started")

    def schedule_stop(self) -> None:
        """Called when the last client disconnects."""
        if self._manager.client_count > 0 or self._stop_timer is not None:
            return
        self._stop_timer = asyncio.create_task(self._stop_after_grace())

    async def _stop_after_grace(self) -> None:
        try:
            await asyncio.sleep(self._settings.poller_grace_period_s)
        except asyncio.CancelledError:
            return  # A client reconnected; do not stop

        if self._manager.client_count == 0:
            await self.stop()
        self._stop_timer = None

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("Poller stopped (no clients connected)")

    async def _run(self) -> None:
        """The polling loop itself."""
        while True:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Unexpected error in polling loop")

            await asyncio.sleep(self._settings.poll_interval_s)

    async def _poll_once(self) -> None:
        try:
            aircraft = await self._client.get_states(self._settings.region)
        except Exception as exc:
            logger.warning("OpenSky fetch failed: %s", exc)
            if self._latest is not None:
                self._latest = self._latest.model_copy(update={"stale": True})
                await self._manager.broadcast(self._latest)
            return

        self._latest = SnapshotMessage(
            fetched_at=int(time.time()),
            stale=False,
            aircraft=aircraft,
        )
        logger.info("Fetched %d aircraft", len(aircraft))
        await self._manager.broadcast(self._latest)