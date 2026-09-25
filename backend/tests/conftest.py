import httpx
import pytest

from app.config import Settings
from app.opensky_client import OpenSkyClient
from tests.factories import FakeOpenSky
from app.connection_manager import ConnectionManager
from app.poller import Poller

@pytest.fixture
def settings() -> Settings:
    return Settings(
        opensky_client_id="test-id",
        opensky_client_secret="test-secret",
        poller_grace_period_s=0.05,
        _env_file=None,
    )


@pytest.fixture
def fake_opensky() -> FakeOpenSky:
    return FakeOpenSky()


@pytest.fixture
async def opensky_client(fake_opensky: FakeOpenSky):
    transport = httpx.MockTransport(fake_opensky.handler)
    async with httpx.AsyncClient(transport=transport) as http:
        yield OpenSkyClient("test-id", "test-secret", http)

@pytest.fixture
def manager() -> ConnectionManager:
    return ConnectionManager()


@pytest.fixture
async def poller(opensky_client, manager, settings):
    poller = Poller(client=opensky_client, manager=manager, settings=settings)
    yield poller
    await poller.close()  # never leave a background task running after a test