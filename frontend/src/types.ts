/** Mirrors backend app/models.py Aircraft */
export interface Aircraft {
    icao24: string;
    callsign: string | null;
    origin_country: string;
    latitude: number;
    longitude: number;
    baro_altitude_m: number | null;
    velocity_ms: number | null;
    heading_deg: number | null;
    vertical_rate_ms: number | null;
    on_ground: boolean;
    last_contact: number;
  }
  
  /** Mirrors backend app/models.py SnapshotMessage */
  export interface SnapshotMessage {
    type: "snapshot";
    fetched_at: number;
    stale: boolean;
    aircraft: Aircraft[];
  }