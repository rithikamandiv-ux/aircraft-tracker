import { describe, expect, it } from "vitest";

import { deriveFeedState } from "./feedState";

const NOW_MS = 1_700_000_100_000; // "now" is Unix second 1_700_000_100
const secondsAgo = (s: number) => 1_700_000_100 - s;

describe("deriveFeedState", () => {
  it("is loading while the socket is still connecting", () => {
    expect(deriveFeedState("connecting", null, false, NOW_MS)).toBe("loading");
  });

  it("is loading when connected but no snapshot has arrived yet", () => {
    expect(deriveFeedState("open", null, false, NOW_MS)).toBe("loading");
  });

  it("is live for a fresh snapshot", () => {
    expect(deriveFeedState("open", secondsAgo(10), false, NOW_MS)).toBe("live");
  });

  it("is stale when the server flags the snapshot", () => {
    expect(deriveFeedState("open", secondsAgo(10), true, NOW_MS)).toBe("stale");
  });

  it("stays live at exactly the 90 second threshold", () => {
    expect(deriveFeedState("open", secondsAgo(90), false, NOW_MS)).toBe("live");
  });

  it("becomes stale one second past the threshold, even if unflagged", () => {
    expect(deriveFeedState("open", secondsAgo(91), false, NOW_MS)).toBe("stale");
  });

  it.each(["reconnecting", "closed"] as const)(
    "is reconnecting when the socket is %s, with or without data",
    (status) => {
      expect(deriveFeedState(status, null, false, NOW_MS)).toBe("reconnecting");
      expect(deriveFeedState(status, secondsAgo(10), false, NOW_MS)).toBe(
        "reconnecting",
      );
    },
  );

  it("reports a lost connection ahead of stale data", () => {
    expect(deriveFeedState("reconnecting", secondsAgo(500), true, NOW_MS)).toBe(
      "reconnecting",
    );
  });
});