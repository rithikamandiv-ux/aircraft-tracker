import type { Aircraft } from "./types";
import { formatAltitude, formatSpeed } from "./format";
import AircraftDetail from "./AircraftDetail";

interface SidebarProps {
  aircraft: Aircraft[];
  selectedIcao: string | null;
  onSelect: (icao24: string | null) => void;
}

export default function Sidebar({ aircraft, selectedIcao, onSelect }: SidebarProps) {
  const selected = aircraft.find((a) => a.icao24 === selectedIcao) ?? null;

  // Sort by callsign so the list order stays stable between updates
  const sorted = [...aircraft].sort((a, b) =>
    (a.callsign ?? a.icao24).localeCompare(b.callsign ?? b.icao24),
  );

  return (
    <aside className="flex w-80 shrink-0 flex-col border-l border-slate-700 bg-slate-900">
      {selected && (
        <AircraftDetail aircraft={selected} onClose={() => onSelect(null)} />
      )}

      <div className="border-b border-slate-700 px-4 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          In range ({aircraft.length})
        </h2>
      </div>

      <ul className="flex-1 overflow-y-auto">
        {sorted.map((a) => {
          const isSelected = a.icao24 === selectedIcao;
          return (
            <li key={a.icao24}>
              <button
                type="button"
                onClick={() => onSelect(isSelected ? null : a.icao24)}
                aria-current={isSelected ? "true" : undefined}
                className={`w-full border-b border-slate-800 px-4 py-2 text-left transition-colors hover:bg-slate-800 focus:bg-slate-800 focus:outline-none focus-visible:ring-1 focus-visible:ring-sky-400 ${
                  isSelected ? "bg-slate-800" : ""
                }`}
              >
                <div className="flex items-baseline justify-between">
                  <span className="font-mono text-sm text-sky-300">
                    {a.callsign ?? a.icao24}
                  </span>
                  <span className="text-xs text-slate-400">
                    {formatAltitude(a.baro_altitude_m)}
                  </span>
                </div>
                <div className="flex items-baseline justify-between text-xs text-slate-500">
                  <span className="truncate">{a.origin_country}</span>
                  <span>{formatSpeed(a.velocity_ms)}</span>
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}