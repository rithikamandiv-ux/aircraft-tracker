import asyncio
import json

import httpx
import pytest

from app.opensky_client import RateLimitedError
from tests.factories import FakeWebSocket, make_state, states_response, wait_until


async def connect_client(manager) -> FakeWebSocket:
    ws = FakeWebSocket()
    await manager.connect(ws)
    return ws


def messages(ws: FakeWebSocket) -> list[dict]:
    return [json.loads(raw) for raw in ws.sent]


# ---- Lifecycle ------------------------------------------------------------


async def test_first_poll_broadcasts_a_snapshot(poller, manager, fake_opensky):
    ws = await connect_client(manager)
    fake_opensky.queue_states(states_response(make_state(icao24="aaa111")))

    poller.ensure_running()
    await wait_until(lambda: ws.sent)

    [message] = messages(ws)
    assert message["stale"] is False
    assert [a["icao24"] for a in message["aircraft"]] == ["aaa111"]


async def test_ensure_running_twice_starts_only_one_loop(poller, fake_opensky):
    fake_opensky.queue_states(states_response())

    poller.ensure_running()
    poller.ensure_running()
    await wait_until(lambda: poller.latest is not None)
    await asyncio.sleep(0.05)  # give a duplicate loop the chance to appear

    assert len(fake_opensky.state_requests) == 1


async def test_stop_cancels_polling(poller, fake_opensky):
    fake_opensky.queue_states(states_response())
    poller.ensure_running()
    await wait_until(lambda: poller.latest is not None)

    await poller.stop()

    assert not poller.is_running


# ---- Grace period ---------------------------------------------------------


async def test_stops_after_grace_period_with_no_clients(poller, fake_opensky):
    fake_opensky.queue_states(states_response())
    poller.ensure_running()
    await wait_until(lambda: poller.latest is not None)

    poller.schedule_stop()

    await wait_until(lambda: not poller.is_running)


async def test_client_returning_during_grace_period_keeps_poller_alive(
    poller, fake_opensky, settings
):
    fake_opensky.queue_states(states_response())
    poller.ensure_running()
    await wait_until(lambda: poller.latest is not None)

    poller.schedule_stop()
    poller.ensure_running()  # a client came back, e.g. a page refresh
    await asyncio.sleep(settings.poller_grace_period_s * 3)

    assert poller.is_running
    assert len(fake_opensky.state_requests) == 1  # the refresh cost no credits


async def test_stop_is_not_scheduled_while_clients_remain(
    poller, manager, fake_opensky, settings
):
    await connect_client(manager)
    fake_opensky.queue_states(states_response())
    poller.ensure_running()
    await wait_until(lambda: poller.latest is not None)

    poller.schedule_stop()
    await asyncio.sleep(settings.poller_grace_period_s * 3)

    assert poller.is_running


# ---- Failure handling -----------------------------------------------------


async def test_failed_fetch_marks_last_snapshot_stale_exactly_once(
    poller, manager, fake_opensky
):
    ws = await connect_client(manager)
    fake_opensky.queue_states(
        states_response(make_state()),
        httpx.Response(503),
        httpx.Response(503),
    )

    await poller._poll_once()
    await poller._poll_once()
    await poller._poll_once()

    assert [m["stale"] for m in messages(ws)] == [False, True]
    assert poller.latest is not None
    assert len(poller.latest.aircraft) == 1  # last good positions are kept


async def test_failed_first_fetch_broadcasts_nothing(poller, manager, fake_opensky):
    ws = await connect_client(manager)
    fake_opensky.queue_states(httpx.Response(503))

    await poller._poll_once()

    assert ws.sent == []
    assert poller.latest is None


async def test_rate_limit_propagates_out_of_a_single_poll(poller, fake_opensky):
    fake_opensky.queue_states(httpx.Response(429))

    with pytest.raises(RateLimitedError):
        await poller._poll_once()


async def test_rate_limit_pauses_the_loop_for_the_server_hint(
    poller, fake_opensky, monkeypatch
):
    fake_opensky.queue_states(
        httpx.Response(429, headers={"X-Rate-Limit-Retry-After-Seconds": "120"})
    )
    requested_sleeps: list[float] = []
    real_sleep = asyncio.sleep

    async def recording_sleep(seconds: float) -> None:
        requested_sleeps.append(seconds)
        await real_sleep(3600)  # park the loop here; fixture teardown cancels it

    monkeypatch.setattr(asyncio, "sleep", recording_sleep)

    poller.ensure_running()
    await wait_until(lambda: requested_sleeps)

    assert requested_sleeps == [120.0]