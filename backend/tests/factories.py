"""Builders for test data, so tests describe only what they care about."""

import asyncio
from collections.abc import Callable

import httpx


def make_state(
    icao24: str = "abc123",
    callsign: str | None = "ALK227  ",
    origin_country: str = "Sri Lanka",
    latitude: float | None = 6.9,
    longitude: float | None = 79.9,
    baro_altitude: float | None = 10_000.0,
    on_ground: bool = False,
    velocity: float | None = 230.0,
    true_track: float | None = 45.0,
    vertical_rate: float | None = 0.0,
    last_contact: int = 1_700_000_005,
) -> list:
    """Build a raw OpenSky state vector: a positional list, as the API sends it."""
    return [
        icao24,  # 0
        callsign,  # 1
        origin_country,  # 2
        1_700_000_000,  # 3  time_position
        last_contact,  # 4
        longitude,  # 5
        latitude,  # 6
        baro_altitude,  # 7
        on_ground,  # 8
        velocity,  # 9
        true_track,  # 10
        vertical_rate,  # 11
        None,  # 12 sensors
        10_100.0,  # 13 geo_altitude
        "1234",  # 14 squawk
        False,  # 15 spi
        0,  # 16 position_source
    ]


def states_response(*states: list) -> httpx.Response:
    return httpx.Response(200, json={"time": 1_700_000_000, "states": list(states)})


class FakeOpenSky:
    """Stands in for OpenSky's auth server and data API.

    Tests queue the responses they want; the fake records every request
    so tests can assert what the client actually sent.
    """

    def __init__(self) -> None:
        self.token_requests = 0
        self.token_expires_in = 1800
        self.state_requests: list[httpx.Request] = []
        self._state_responses: list[httpx.Response] = []

    def queue_states(self, *responses: httpx.Response) -> None:
        self._state_responses.extend(responses)

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            self.token_requests += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"token-{self.token_requests}",
                    "expires_in": self.token_expires_in,
                },
            )

        if request.url.path == "/api/states/all":
            self.state_requests.append(request)
            if not self._state_responses:
                raise AssertionError("Unexpected states request: nothing queued")
            return self._state_responses.pop(0)

        raise AssertionError(f"Unexpected request: {request.url}")


# Captured at import so tests that patch asyncio.sleep cannot affect it
_real_sleep = asyncio.sleep


async def wait_until(predicate: Callable[[], object], timeout: float = 1.0) -> None:
    """Poll a condition until it holds, instead of sleeping a fixed time."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() > deadline:
            raise AssertionError("Condition not met within timeout")
        await _real_sleep(0.01)


class FakeWebSocket:
    """Records what the server sends; can be told to fail like a dead client."""

    def __init__(self, fail_on_send: bool = False) -> None:
        self.accepted = False
        self.sent: list[str] = []
        self._fail_on_send = fail_on_send

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, data: str) -> None:
        if self._fail_on_send:
            raise RuntimeError("Connection closed")
        self.sent.append(data)
