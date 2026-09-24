import type { FeedState } from "./feedState";
import { formatAge } from "./format";

interface FeedBannerProps {
  feed: FeedState;
  fetchedAt: number | null;
  nowMs: number;
}

export default function FeedBanner({ feed, fetchedAt, nowMs }: FeedBannerProps) {
  if (feed === "stale" && fetchedAt !== null) {
    return (
      <div className="border-b border-amber-900 bg-amber-950/60 px-4 py-2 text-sm text-amber-200">
        Live data is temporarily unavailable. Showing last known positions from{" "}
        {formatAge(fetchedAt, nowMs)}.
      </div>
    );
  }

  if (feed === "reconnecting") {
    return (
      <div className="border-b border-rose-900 bg-rose-950/60 px-4 py-2 text-sm text-rose-200">
        Connection to the server was lost. Reconnecting automatically
        {fetchedAt !== null ? "; positions shown may be out of date." : "."}
      </div>
    );
  }

  return null;
}