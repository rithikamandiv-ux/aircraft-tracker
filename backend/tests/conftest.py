import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.connection_manager import ConnectionManager
from app.main import create_app
from app.opensky_client import OpenSkyClient
from app.poller import Poller
from tests.factories import FakeOpenSky


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


@pytest.fixture
def client(settings, fake_opensky):
    app = create_app(
        settings=settings,
        transport=httpx.MockTransport(fake_opensky.handler),
    )
    with TestClient(app) as client:
        yield client
