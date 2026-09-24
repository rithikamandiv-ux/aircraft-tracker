import { divIcon, type DivIcon } from "leaflet";
import { memo, useEffect, useRef } from "react";
import { MapContainer, Marker, TileLayer, useMap } from "react-leaflet";

import type { Aircraft } from "./types";

const SRI_LANKA_CENTER: [number, number] = [7.5, 80.5];
const INITIAL_ZOOM = 6;

interface MapViewProps {
  aircraft: Aircraft[];
  selectedIcao: string | null;
  onSelect: (icao24: string | null) => void;
}

function createPlaneIcon(headingDeg: number, isSelected: boolean): DivIcon {
  const color = isSelected ? "#38bdf8" : "#e2e8f0";
  return divIcon({
    className: "",
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    html: `
      <svg viewBox="0 0 24 24" width="24" height="24"
           style="transform: rotate(${headingDeg}deg);">
        <path d="M12 2 L14 11 L22 14 L22 16 L14 14.5 L13.5 20 L16 21.5 L16 22.5
                 L12 21.5 L8 22.5 L8 21.5 L10.5 20 L10 14.5 L2 16 L2 14 L10 11 Z"
              fill="${color}" stroke="#0f172a" stroke-width="0.5" />
      </svg>`,
  });
}

// At most 72 headings x 2 states = 144 entries, so the cache stays small.
const iconCache = new Map<string, DivIcon>();

function getPlaneIcon(headingDeg: number, isSelected: boolean): DivIcon {
  const rounded = (Math.round(headingDeg / 5) * 5) % 360;
  const key = `${rounded}:${isSelected}`;

  let icon = iconCache.get(key);
  if (!icon) {
    icon = createPlaneIcon(rounded, isSelected);
    iconCache.set(key, icon);
  }
  return icon;
}

/** Flies to an aircraft once, when it becomes selected. */
function MapController({
  aircraft,
  selectedIcao,
}: {
  aircraft: Aircraft[];
  selectedIcao: string | null;
}) {
  const map = useMap();
  const lastFlownRef = useRef<string | null>(null);

  useEffect(() => {
    if (selectedIcao === null) {
      lastFlownRef.current = null;
      return;
    }
    if (selectedIcao === lastFlownRef.current) return; // Already flew here

    const target = aircraft.find((a) => a.icao24 === selectedIcao);
    if (!target) return;

    lastFlownRef.current = selectedIcao;
    map.flyTo([target.latitude, target.longitude], Math.max(map.getZoom(), 8), {
      duration: 0.8,
    });
  }, [aircraft, selectedIcao, map]);

  return null;
}

function MapView({ aircraft, selectedIcao, onSelect }: MapViewProps) {
  return (
    <MapContainer
      center={SRI_LANKA_CENTER}
      zoom={INITIAL_ZOOM}
      className="isolate h-full w-full bg-slate-900"
      worldCopyJump
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={19}
      />

      <MapController aircraft={aircraft} selectedIcao={selectedIcao} />

      {aircraft.map((a) => (
        <Marker
          key={a.icao24}
          position={[a.latitude, a.longitude]}
          icon={getPlaneIcon(a.heading_deg ?? 0, a.icao24 === selectedIcao)}
          eventHandlers={{ click: () => onSelect(a.icao24) }}
        />
      ))}
    </MapContainer>
  );
}

export default memo(MapView);