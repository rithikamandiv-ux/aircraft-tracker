import { useAircraftSocket } from "./useAircraftSocket";

const WS_URL = "ws://127.0.0.1:8000/ws";

export default function App() {
  const { aircraft, fetchedAt, stale, status } = useAircraftSocket(WS_URL);

  return (
    <div className="min-h-screen bg-slate-900 p-8 font-mono text-slate-200">
      <h1 className="mb-4 text-2xl font-bold text-sky-400">Aircraft Tracker</h1>
      <p>Status: {status}</p>
      <p>Aircraft: {aircraft.length}</p>
      <p>Stale: {String(stale)}</p>
      <p>
        Fetched: {fetchedAt ? new Date(fetchedAt * 1000).toLocaleTimeString() : "never"}
      </p>
      <ul className="mt-4 space-y-1">
        {aircraft.map((a) => (
          <li key={a.icao24}>
            {a.callsign ?? "(no callsign)"} — {a.origin_country}
          </li>
        ))}
      </ul>
    </div>
  );
}