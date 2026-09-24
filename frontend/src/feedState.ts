import type { ConnectionStatus } from "./useAircraftSocket";

export type FeedState = "loading" | "live" | "stale" | "reconnecting";

// Three missed 30-second polls. Must stay in sync with the backend interval.
const STALE_AFTER_S = 90;

export function deriveFeedState(
  status: ConnectionStatus,
  fetchedAt: number | null,
  stale: boolean,
  nowMs: number,
): FeedState {
  if (status === "reconnecting" || status === "closed") return "reconnecting";
  if (status === "connecting" || fetchedAt === null) return "loading";
  if (stale || nowMs / 1000 - fetchedAt > STALE_AFTER_S) return "stale";
  return "live";
}