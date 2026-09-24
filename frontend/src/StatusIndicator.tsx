import type { FeedState } from "./feedState";
import { formatAge } from "./format";

const STYLES: Record<FeedState, { dot: string; label: string }> = {
  loading: { dot: "bg-slate-500 animate-pulse", label: "Connecting" },
  live: { dot: "bg-emerald-400", label: "Live" },
  stale: { dot: "bg-amber-400", label: "Delayed" },
  reconnecting: { dot: "bg-rose-400 animate-pulse", label: "Reconnecting" },
};

interface StatusIndicatorProps {
  feed: FeedState;
  fetchedAt: number | null;
  count: number;
  nowMs: number;
}

export default function StatusIndicator({
  feed,
  fetchedAt,
  count,
  nowMs,
}: StatusIndicatorProps) {
  const { dot, label } = STYLES[feed];

  return (
    <div className="flex items-center gap-3 text-sm text-slate-400">
      <span role="status" aria-live="polite" className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
        <span className="text-slate-200">{label}</span>
      </span>
      {fetchedAt !== null && (
        <span>
          {count} aircraft &middot; updated {formatAge(fetchedAt, nowMs)}
        </span>
      )}
    </div>
  );
}