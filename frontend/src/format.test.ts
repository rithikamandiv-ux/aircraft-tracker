import { describe, expect, it } from "vitest";

import {
  formatAge,
  formatAltitude,
  formatHeading,
  formatSpeed,
  formatVerticalRate,
} from "./format";

describe("formatAltitude", () => {
  it("converts metres to feet, rounded to the nearest 100", () => {
    // 10,000 m = 32,808 ft, which rounds to 32,800
    expect(formatAltitude(10_000)).toBe(`${(32_800).toLocaleString()} ft`);
  });

  it("shows unknown rather than zero when altitude is missing", () => {
    expect(formatAltitude(null)).toBe("unknown");
  });

  it("keeps a genuine zero as zero", () => {
    expect(formatAltitude(0)).toBe("0 ft");
  });
});

describe("formatSpeed", () => {
  it("converts metres per second to whole knots", () => {
    expect(formatSpeed(100)).toBe("194 kt"); // 194.38 kt
  });

  it("shows unknown when speed is missing", () => {
    expect(formatSpeed(null)).toBe("unknown");
  });
});

describe("formatHeading", () => {
  it.each([
    [45, "045 deg (NE)"],
    [180, "180 deg (S)"],
    [22, "022 deg (N)"], // just below the N/NE boundary at 22.5
    [23, "023 deg (NE)"], // just above it
  ])("formats %d as %s", (input, expected) => {
    expect(formatHeading(input)).toBe(expected);
  });

  it("shows north as 360 whichever side of north it rounds from", () => {
    expect(formatHeading(0)).toBe("360 deg (N)");
    expect(formatHeading(359.6)).toBe("360 deg (N)");
  });

  it("shows unknown when heading is missing", () => {
    expect(formatHeading(null)).toBe("unknown");
  });
});

describe("formatVerticalRate", () => {
  it.each([0, 0.3])("reports %d m/s as level flight", (rate) => {
    expect(formatVerticalRate(rate)).toBe("level");
  });

  it("reports a climb in feet per minute", () => {
    expect(formatVerticalRate(2)).toBe("climbing 400 ft/min"); // 393.7 ft/min
  });

  it("reports a descent without a minus sign", () => {
    expect(formatVerticalRate(-2)).toBe("descending 400 ft/min");
  });

  it("shows unknown when the rate is missing", () => {
    expect(formatVerticalRate(null)).toBe("unknown");
  });
});

describe("formatAge", () => {
  const NOW_MS = 1_700_000_042_000;

  it("shows seconds under a minute", () => {
    expect(formatAge(1_700_000_000, NOW_MS)).toBe("42s ago");
  });

  it("switches to minutes at exactly 60 seconds", () => {
    expect(formatAge(1_700_000_042 - 59, NOW_MS)).toBe("59s ago");
    expect(formatAge(1_700_000_042 - 60, NOW_MS)).toBe("1m ago");
  });

  it("never shows a negative age when the clocks disagree", () => {
    // A timestamp slightly in the future, e.g. server clock ahead of the browser
    expect(formatAge(1_700_000_050, NOW_MS)).toBe("0s ago");
  });
});