import time

import httpx

from app.models import Aircraft, BoundingBox, normalize_state

TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network"
    "/protocol/openid-connect/token"
)
STATES_URL = "https://opensky-network.org/api/states/all"
TOKEN_REFRESH_MARGIN_S = 60


class OpenSkyClient:
    def __init__(self, client_id: str, client_secret: str, http: httpx.AsyncClient):
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http
        self._token: str | None = None
        self._token_expires_at = 0.0

    async def _get_token(self) -> str:
        # Reuse the cached token unless it is about to expire
        if self._token and time.monotonic() < self._token_expires_at - TOKEN_REFRESH_MARGIN_S:
            return self._token

        response = await self._http.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        payload = response.json()

        self._token = payload["access_token"]
        self._token_expires_at = time.monotonic() + payload["expires_in"]
        return self._token

    async def get_states(self, bbox: BoundingBox) -> list[Aircraft]:
        token = await self._get_token()
        response = await self._http.get(
            STATES_URL,
            params=bbox.model_dump(),
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()

        raw_states = response.json().get("states") or []
        return [a for s in raw_states if (a := normalize_state(s)) is not None]