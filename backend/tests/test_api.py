import pytest
from starlette.websockets import WebSocketDisconnect

from tests.factories import make_state, states_response

ALLOWED_ORIGIN = "http://localhost:5173"


def test_health_before_any_client(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "connected_clients": 0,
        "poller_running": False,
        "last_fetch_at": None,
        "aircraft_count": 0,
        "stale": None,
    }


def test_websocket_receives_live_snapshot(client, fake_opensky):
    fake_opensky.queue_states(states_response(make_state(icao24="aaa111")))

    with client.websocket_connect("/ws", headers={"origin": ALLOWED_ORIGIN}) as ws:
        message = ws.receive_json()

    assert message["type"] == "snapshot"
    assert [a["icao24"] for a in message["aircraft"]] == ["aaa111"]


def test_websocket_without_origin_is_allowed(client, fake_opensky):
    # Non-browser clients (scripts, CLI tools) send no Origin header
    fake_opensky.queue_states(states_response())

    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "snapshot"


def test_websocket_from_unknown_origin_is_rejected(client, fake_opensky):
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect("/ws", headers={"origin": "https://evil.example"}),
    ):
        pass

    assert exc_info.value.code == 1008
    assert fake_opensky.state_requests == []  # rejected clients spend no credits


def test_second_client_gets_cached_snapshot_without_new_fetch(client, fake_opensky):
    fake_opensky.queue_states(states_response(make_state()))
    headers = {"origin": ALLOWED_ORIGIN}

    with client.websocket_connect("/ws", headers=headers) as first:
        first.receive_json()
        with client.websocket_connect("/ws", headers=headers) as second:
            cached = second.receive_json()

    assert len(cached["aircraft"]) == 1
    assert len(fake_opensky.state_requests) == 1  # fan-out: one fetch, two viewers


def test_health_reflects_connected_client(client, fake_opensky):
    fake_opensky.queue_states(states_response(make_state()))

    with client.websocket_connect("/ws", headers={"origin": ALLOWED_ORIGIN}) as ws:
        ws.receive_json()
        health = client.get("/health").json()

    assert health["connected_clients"] == 1
    assert health["poller_running"] is True
    assert health["aircraft_count"] == 1


def test_cors_allows_the_frontend_origin(client):
    response = client.get("/health", headers={"origin": ALLOWED_ORIGIN})

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_cors_omits_header_for_unknown_origin(client):
    response = client.get("/health", headers={"origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers
