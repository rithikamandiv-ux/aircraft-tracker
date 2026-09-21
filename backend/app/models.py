from pydantic import BaseModel


class BoundingBox(BaseModel):
    lamin: float
    lomin: float
    lamax: float
    lomax: float


class Aircraft(BaseModel):
    icao24: str                     # unique transponder address
    callsign: str | None
    origin_country: str
    latitude: float
    longitude: float
    baro_altitude_m: float | None
    velocity_ms: float | None
    heading_deg: float | None       # OpenSky calls this "true_track"
    vertical_rate_ms: float | None
    on_ground: bool
    last_contact: int               # Unix timestamp


def normalize_state(state: list) -> Aircraft | None:
    """Convert one raw OpenSky state vector into an Aircraft.
    Returns None if the aircraft has no known position."""
    longitude, latitude = state[5], state[6]
    if latitude is None or longitude is None:
        return None

    callsign = state[1].strip() if state[1] else None

    return Aircraft(
        icao24=state[0],
        callsign=callsign or None,
        origin_country=state[2],
        latitude=latitude,
        longitude=longitude,
        baro_altitude_m=state[7],
        velocity_ms=state[9],
        heading_deg=state[10],
        vertical_rate_ms=state[11],
        on_ground=state[8],
        last_contact=state[4],
    )