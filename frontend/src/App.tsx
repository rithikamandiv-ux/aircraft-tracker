import { useState } from "react";

import MapView from "./MapView";
import Sidebar from "./Sidebar";
import { useAircraftSocket } from "./useAircraftSocket";

const WS_URL = "ws://127.0.0.1:8000/ws";

export default function App() {
  const { aircraft, status } = useAircraftSocket(WS_URL);
  const [selectedIcao, setSelectedIcao] = useState<string | null>(null);

  return (
    <div className="flex h-screen flex-col bg-slate-900 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
        <h1 className="text-lg font-bold text-sky-400">Aircraft Tracker</h1>
        <span className="text-sm text-slate-400">
          {aircraft.length} aircraft &middot; {status}
        </span>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1">
          <MapView
            aircraft={aircraft}
            selectedIcao={selectedIcao}
            onSelect={setSelectedIcao}
          />
        </main>

        <Sidebar
          aircraft={aircraft}
          selectedIcao={selectedIcao}
          onSelect={setSelectedIcao}
        />
      </div>
    </div>
  );
}