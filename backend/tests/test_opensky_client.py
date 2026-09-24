import httpx
import pytest

from app.models import BoundingBox
from app.opensky_client import RateLimitedError
from tests.factories import make_state, states_response

REGION = BoundingBox(lamin=2.0, lomin=72.0, lamax=16.0, lomax=88.0)


async def test_returns_normalized_aircraft(opensky_client, fake_opensky):
    fake_opensky.queue_states(
        states_response(
            make_state(icao24="aaa111", callsign="ALK227  "),
            make_state(icao24="bbb222", latitude=None),  # no position: dropped
        )
    )

    aircraft = await opensky_client.get_states(REGION)

    assert [a.icao24 for a in aircraft] == ["aaa111"]
    assert aircraft[0].callsign == "ALK227"


async def test_sends_region_and_bearer_token(opensky_client, fake_opensky):
    fake_opensky.queue_states(states_response())

    await opensky_client.get_states(REGION)

    request = fake_opensky.state_requests[0]
    assert request.headers["Authorization"] == "Bearer token-1"
    assert dict(request.url.params) == {
        "lamin": "2.0",
        "lomin": "72.0",
        "lamax": "16.0",
        "lomax": "88.0",
    }


async def test_null_states_means_no_aircraft(opensky_client, fake_opensky):
    # OpenSky sends "states": null, not [], when a region is empty
    fake_opensky.queue_states(httpx.Response(200, json={"time": 0, "states": None}))

    assert await opensky_client.get_states(REGION) == []


async def test_reuses_cached_token(opensky_client, fake_opensky):
    fake_opensky.queue_states(states_response(), states_response())

    await opensky_client.get_states(REGION)
    await opensky_client.get_states(REGION)

    assert fake_opensky.token_requests == 1


async def test_refreshes_token_inside_expiry_margin(opensky_client, fake_opensky):
    # A 30s lifetime is inside the 60s refresh margin, so it is never reused
    fake_opensky.token_expires_in = 30
    fake_opensky.queue_states(states_response(), states_response())

    await opensky_client.get_states(REGION)
    await opensky_client.get_states(REGION)

    assert fake_opensky.token_requests == 2


async def test_retries_once_with_fresh_token_after_401(opensky_client, fake_opensky):
    fake_opensky.queue_states(httpx.Response(401), states_response(make_state()))

    aircraft = await opensky_client.get_states(REGION)

    assert len(aircraft) == 1
    assert fake_opensky.token_requests == 2
    assert fake_opensky.state_requests[1].headers["Authorization"] == "Bearer token-2"


async def test_gives_up_after_second_401(opensky_client, fake_opensky):
    fake_opensky.queue_states(httpx.Response(401), httpx.Response(401))

    with pytest.raises(httpx.HTTPStatusError):
        await opensky_client.get_states(REGION)

    assert len(fake_opensky.state_requests) == 2  # bounded: no retry loop


@pytest.mark.parametrize(
    ("headers", "expected_wait"),
    [
        ({"X-Rate-Limit-Retry-After-Seconds": "120"}, 120.0),
        ({"Retry-After": "30"}, 30.0),
        ({"X-Rate-Limit-Retry-After-Seconds": "-5"}, 0.0),
        ({"Retry-After": "soon"}, 3600.0),
        ({}, 3600.0),
    ],
)
async def test_429_raises_rate_limited_with_retry_hint(
    opensky_client, fake_opensky, headers, expected_wait
):
    fake_opensky.queue_states(httpx.Response(429, headers=headers))

    with pytest.raises(RateLimitedError) as exc_info:
        await opensky_client.get_states(REGION)

    assert exc_info.value.retry_after_s == expected_wait
    assert len(fake_opensky.state_requests) == 1  # never retry into a rate limit


async def test_server_error_raises(opensky_client, fake_opensky):
    fake_opensky.queue_states(httpx.Response(503))

    with pytest.raises(httpx.HTTPStatusError):
        await opensky_client.get_states(REGION)