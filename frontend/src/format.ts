const METRES_TO_FEET = 3.28084;
const MS_TO_KNOTS = 1.94384;

/** Barometric altitude in feet, rounded to the nearest 100. */
export function formatAltitude(metres: number | null): string {
  if (metres === null) return "unknown";
  const feet = Math.round((metres * METRES_TO_FEET) / 100) * 100;
  return `${feet.toLocaleString()} ft`;
}

export function formatSpeed(metresPerSecond: number | null): string {
  if (metresPerSecond === null) return "unknown";
  return `${Math.round(metresPerSecond * MS_TO_KNOTS)} kt`;
}

/** Heading as degrees plus compass point, e.g. "045 deg (NE)". */
export function formatHeading(degrees: number | null): string {
  if (degrees === null) return "unknown";
  const points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(degrees / 45) % 8;
  return `${Math.round(degrees).toString().padStart(3, "0")} deg (${points[index]})`;
}

/** Vertical rate described in words, since the raw number means little. */
export function formatVerticalRate(metresPerSecond: number | null): string {
  if (metresPerSecond === null) return "unknown";
  const feetPerMin = Math.round((metresPerSecond * METRES_TO_FEET * 60) / 50) * 50;
  if (Math.abs(feetPerMin) < 100) return "level";
  const direction = feetPerMin > 0 ? "climbing" : "descending";
  return `${direction} ${Math.abs(feetPerMin).toLocaleString()} ft/min`;
}

/** Seconds since a Unix timestamp, described in words. */
export function formatAge(unixSeconds: number): string {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - unixSeconds));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ago`;
}