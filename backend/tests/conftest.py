import httpx
import pytest

from app.config import Settings
from app.opensky_client import OpenSkyClient
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