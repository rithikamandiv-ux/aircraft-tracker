import asyncio
import os

import httpx
from dotenv import load_dotenv

from app.models import BoundingBox
from app.opensky_client import OpenSkyClient

SRI_LANKA_REGION = BoundingBox(lamin=4.0, lomin=77.0, lamax=11.0, lomax=84.0)


async def main() -> None:
    load_dotenv()
    async with httpx.AsyncClient(timeout=15.0) as http:
        client = OpenSkyClient(
            client_id=os.environ["OPENSKY_CLIENT_ID"],
            client_secret=os.environ["OPENSKY_CLIENT_SECRET"],
            http=http,
        )
        aircraft = await client.get_states(SRI_LANKA_REGION)

    print(f"Aircraft in region: {len(aircraft)}\n")
    for a in aircraft:
        alt = f"{a.baro_altitude_m:.0f} m" if a.baro_altitude_m is not None else "n/a"
        print(f"{a.callsign or '(no callsign)':<10} {a.origin_country:<20} alt={alt}")


if __name__ == "__main__":
    asyncio.run(main())