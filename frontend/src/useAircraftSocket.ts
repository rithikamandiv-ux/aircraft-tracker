import { useCallback, useEffect, useRef, useState } from "react";

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

  // Refs hold values that must survive re-renders without causing them
  const socketRef = useRef<WebSocket | null>(null);
  const retryDelayRef = useRef(INITIAL_RETRY_MS);
  const retryTimerRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (!shouldReconnectRef.current) return;

    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => {
      retryDelayRef.current = INITIAL_RETRY_MS; // Reset back-off on success
      setStatus("open");
    };

    socket.onmessage = (event) => {
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

    socket.onerror = () => {
      // onclose always follows, so reconnection is handled there
      socket.close();
    };

    socket.onclose = () => {
      socketRef.current = null;
      if (!shouldReconnectRef.current) {
        setStatus("closed");
        return;
      }

      setStatus("reconnecting");
      retryTimerRef.current = window.setTimeout(connect, retryDelayRef.current);
      retryDelayRef.current = Math.min(retryDelayRef.current * 2, MAX_RETRY_MS);
    };
  }, [url]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      // Cleanup: stop reconnecting and close the socket
      shouldReconnectRef.current = false;

      if (retryTimerRef.current !== null) {
        window.clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }

      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [connect]);

  return { aircraft, fetchedAt, stale, status };
}