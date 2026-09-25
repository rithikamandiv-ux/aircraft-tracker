import logging
import time

import httpx

from app.models import Aircraft, BoundingBox, normalize_state

logger = logging.getLogger(__name__)

TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network"
    "/protocol/openid-connect/token"
)
STATES_URL = "https://opensky-network.org/api/states/all"
TOKEN_REFRESH_MARGIN_S = 60


class RateLimitedError(Exception):
    """Raised when OpenSky reports the credit budget is exhausted."""

    def __init__(self, retry_after_s: float) -> None:
        super().__init__(f"Rate limited; retry in {retry_after_s:.0f}s")
        self.retry_after_s = retry_after_s


class OpenSkyClient:
    def __init__(self, client_id: str, client_secret: str, http: httpx.AsyncClient):
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http
        self._token: str | None = None
        self._token_expires_at = 0.0

    def _invalidate_token(self) -> None:
        self._token = None
        self._token_expires_at = 0.0

    async def _get_token(self) -> str:
        # Reuse the cached token unless it is about to expire
        if (
            self._token
            and time.monotonic() < self._token_expires_at - TOKEN_REFRESH_MARGIN_S
        ):
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
        response = await self._request_states(bbox)

        # The cached token may have been revoked early: refresh once and retry
        if response.status_code == 401:
            logger.info("Token rejected; refreshing and retrying once")
            self._invalidate_token()
            response = await self._request_states(bbox)

        if response.status_code == 429:
            raise RateLimitedError(self._retry_after_seconds(response))

        response.raise_for_status()
        raw_states = response.json().get("states") or []
        return [a for s in raw_states if (a := normalize_state(s)) is not None]

    async def _request_states(self, bbox: BoundingBox) -> httpx.Response:
        token = await self._get_token()
        return await self._http.get(
            STATES_URL,
            params=bbox.model_dump(),
            headers={"Authorization": f"Bearer {token}"},
        )

    @staticmethod
    def _retry_after_seconds(response: httpx.Response) -> float:
        """Read OpenSky's retry hint, falling back to a conservative default."""
        for header in ("X-Rate-Limit-Retry-After-Seconds", "Retry-After"):
            raw = response.headers.get(header)
            if raw:
                try:
                    return max(float(raw), 0.0)
                except ValueError:
                    pass
        return 3600.0  # Unknown: wait an hour rather than hammering the API
