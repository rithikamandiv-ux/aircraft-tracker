import pytest

from app.models import normalize_state
from tests.factories import make_state


def test_maps_fields_and_strips_callsign_padding():
    aircraft = normalize_state(
        make_state(callsign="ALK227  ", latitude=6.9, longitude=79.9, true_track=45.0)
    )

    assert aircraft is not None
    assert aircraft.callsign == "ALK227"
    assert (aircraft.latitude, aircraft.longitude) == (6.9, 79.9)
    assert aircraft.heading_deg == 45.0


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(None, 79.9), (6.9, None), (None, None)],
)
def test_aircraft_without_position_is_dropped(latitude, longitude):
    assert normalize_state(make_state(latitude=latitude, longitude=longitude)) is None


@pytest.mark.parametrize("callsign", [None, "", "   "])
def test_blank_callsign_becomes_none(callsign):
    aircraft = normalize_state(make_state(callsign=callsign))

    assert aircraft is not None
    assert aircraft.callsign is None


def test_missing_measurements_stay_none_rather_than_zero():
    aircraft = normalize_state(
        make_state(baro_altitude=None, velocity=None, true_track=None)
    )

    assert aircraft is not None
    assert aircraft.baro_altitude_m is None
    assert aircraft.velocity_ms is None
    assert aircraft.heading_deg is None
