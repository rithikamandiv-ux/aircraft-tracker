import { useEffect, useState } from "react";

import type { Aircraft, SnapshotMessage } from "./types";

export type ConnectionStatus = "connecting" | "open" | "reconnecting" | "closed";

interface AircraftSocketState {
  aircraft: Aircraft[];
  fetchedAt: number | null;
  stale: boolean;
  status: ConnectionStatus;
}

const INITIAL_RETRY_MS = 1_000;
const MAX_RETRY_MS = 30_000;

export function useAircraftSocket(url: string): AircraftSocketState {
  const [aircraft, setAircraft] = useState<Aircraft[]>([]);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);
  const [stale, setStale] = useState(false);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  useEffect(() => {
    // Everything here belongs to this one run of the effect. Cleanup flips
    // `disposed`, and every socket and timer this run created goes quiet,
    // even if its events fire later.
    let disposed = false;
    let socket: WebSocket | null = null;
    let retryTimer: number | undefined;
    let retryDelay = INITIAL_RETRY_MS;

    function connect() {
      if (disposed) return;

      const ws = new WebSocket(url);
      socket = ws;

      ws.onopen = () => {
        if (disposed) return;
        retryDelay = INITIAL_RETRY_MS; // Reset back-off on success
        setStatus("open");
      };

      ws.onmessage = (event) => {
        if (disposed) return;
        try {
          const message: SnapshotMessage = JSON.parse(event.data);
          if (message.type !== "snapshot") return;
          setAircraft(message.aircraft);
          setFetchedAt(message.fetched_at);
          setStale(message.stale);
        } catch (error) {
          console.error("Failed to parse server message", error);
        }
      };

      ws.onerror = () => {
        ws.close(); // onclose follows and handles reconnection
      };

      ws.onclose = () => {
        if (disposed) return; // closed by our own cleanup: stay closed
        setStatus("reconnecting");
        retryTimer = window.setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, MAX_RETRY_MS);
      };
    }

    connect();

    return () => {
      disposed = true;
      window.clearTimeout(retryTimer);
      socket?.close();
    };
  }, [url]);

  return { aircraft, fetchedAt, stale, status };
}