import { useState } from "react";
import FeedBanner from "./FeedBanner";
import MapView from "./MapView";
import Sidebar from "./Sidebar";
import StatusIndicator from "./StatusIndicator";
import { deriveFeedState } from "./feedState";
import { useAircraftSocket } from "./useAircraftSocket";
import { useNow } from "./useNow";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://127.0.0.1:8000/ws";

export default function App() {
  const { aircraft, fetchedAt, stale, status } = useAircraftSocket(WS_URL);
  const [selectedIcao, setSelectedIcao] = useState<string | null>(null);
  const nowMs = useNow(1000);

  const feed = deriveFeedState(status, fetchedAt, stale, nowMs);

  const [prevAircraft, setPrevAircraft] = useState(aircraft);

  // When a new snapshot arrives, drop a selection whose aircraft has left the
  // region. Adjusting state during render means React re-renders immediately,
  // before anything is committed, so no frame ever shows a dangling selection.
  if (aircraft !== prevAircraft) {
    setPrevAircraft(aircraft);
    if (selectedIcao !== null && !aircraft.some((a) => a.icao24 === selectedIcao)) {
      setSelectedIcao(null);
    }
  }

  const mapOverlay =
    feed === "loading"
      ? "Connecting to live feed..."
      : aircraft.length === 0 && feed !== "reconnecting"
        ? "No aircraft in range right now"
        : null;

  return (
    <div className="flex h-screen flex-col bg-slate-900 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
        <h1 className="text-lg font-bold text-sky-400">Aircraft Tracker</h1>
        <StatusIndicator
          feed={feed}
          fetchedAt={fetchedAt}
          count={aircraft.length}
          nowMs={nowMs}
        />
      </header>

      <FeedBanner feed={feed} fetchedAt={fetchedAt} nowMs={nowMs} />

      <div className="flex flex-1 overflow-hidden">
        <main className="relative flex-1">
          <MapView
            aircraft={aircraft}
            selectedIcao={selectedIcao}
            onSelect={setSelectedIcao}
          />
          {mapOverlay && (
            <div className="pointer-events-none absolute inset-x-0 top-4 z-10 flex justify-center">
              <div className="rounded-full bg-slate-900/85 px-4 py-2 text-sm text-slate-300 shadow-lg">
                {mapOverlay}
              </div>
            </div>
          )}
        </main>

        <Sidebar
          aircraft={aircraft}
          selectedIcao={selectedIcao}
          onSelect={setSelectedIcao}
          feed={feed}
        />
      </div>
    </div>
  );
}