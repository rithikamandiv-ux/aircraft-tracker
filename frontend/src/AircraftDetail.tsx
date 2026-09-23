import type { Aircraft } from "./types";
import {
  formatAge,
  formatAltitude,
  formatHeading,
  formatSpeed,
  formatVerticalRate,
} from "./format";

interface AircraftDetailProps {
  aircraft: Aircraft;
  onClose: () => void;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 py-1">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-mono text-slate-200">{value}</dd>
    </div>
  );
}

export default function AircraftDetail({ aircraft, onClose }: AircraftDetailProps) {
  return (
    <section className="border-b border-slate-700 bg-slate-800/60 p-4">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h2 className="font-mono text-lg font-bold text-sky-300">
            {aircraft.callsign ?? "No callsign"}
          </h2>
          <p className="text-xs text-slate-400">{aircraft.origin_country}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="rounded px-2 py-1 text-slate-400 hover:bg-slate-700 hover:text-slate-200 focus-visible:ring-1 focus-visible:ring-sky-400"
        >
          &times;
        </button>
      </div>

      <dl className="text-sm">
        <Row label="Altitude" value={formatAltitude(aircraft.baro_altitude_m)} />
        <Row label="Speed" value={formatSpeed(aircraft.velocity_ms)} />
        <Row label="Heading" value={formatHeading(aircraft.heading_deg)} />
        <Row label="Vertical" value={formatVerticalRate(aircraft.vertical_rate_ms)} />
        <Row label="Status" value={aircraft.on_ground ? "On ground" : "Airborne"} />
        <Row label="ICAO24" value={aircraft.icao24} />
        <Row label="Last seen" value={formatAge(aircraft.last_contact)} />
      </dl>
    </section>
  );
}