import json

from app.models import SnapshotMessage
from tests.factories import FakeWebSocket


def snapshot() -> SnapshotMessage:
    return SnapshotMessage(fetched_at=1_700_000_000, aircraft=[])


async def test_connect_accepts_and_tracks_client(manager):
    ws = FakeWebSocket()

    await manager.connect(ws)

    assert ws.accepted
    assert manager.client_count == 1


async def test_disconnect_is_idempotent(manager):
    ws = FakeWebSocket()
    await manager.connect(ws)

    manager.disconnect(ws)
    manager.disconnect(ws)  # a second call must be harmless

    assert manager.client_count == 0


async def test_broadcast_sends_identical_payload_to_every_client(manager):
    first, second = FakeWebSocket(), FakeWebSocket()
    await manager.connect(first)
    await manager.connect(second)

    await manager.broadcast(snapshot())

    assert len(first.sent) == 1
    assert first.sent == second.sent
    assert json.loads(first.sent[0])["type"] == "snapshot"


async def test_failing_client_is_dropped_without_affecting_others(manager):
    healthy, broken = FakeWebSocket(), FakeWebSocket(fail_on_send=True)
    await manager.connect(healthy)
    await manager.connect(broken)

    await manager.broadcast(snapshot())
    await manager.broadcast(snapshot())

    assert len(healthy.sent) == 2
    assert manager.client_count == 1


async def test_broadcast_with_no_clients_does_nothing(manager):
    await manager.broadcast(snapshot())

    assert manager.client_count == 0
