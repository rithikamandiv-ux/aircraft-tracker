import { divIcon } from "leaflet";
import { MapContainer, Marker, TileLayer, useMap } from "react-leaflet";
import { useEffect, useMemo } from "react";

import type { Aircraft } from "./types";

const SRI_LANKA_CENTER: [number, number] = [7.5, 80.5];
const INITIAL_ZOOM = 6;

interface MapViewProps {
  aircraft: Aircraft[];
  selectedIcao: string | null;
  onSelect: (icao24: string) => void;
}

/** Builds a rotated plane icon. Memoised per heading/selection combination. */
function createPlaneIcon(headingDeg: number, isSelected: boolean) {
  const color = isSelected ? "#38bdf8" : "#e2e8f0";
  return divIcon({
    className: "", // Remove Leaflet's default styling
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    html: `
      <svg viewBox="0 0 24 24" width="24" height="24"
           style="transform: rotate(${headingDeg}deg); transition: transform 0.3s;">
        <path d="M12 2 L14 11 L22 14 L22 16 L14 14.5 L13.5 20 L16 21.5 L16 22.5
                 L12 21.5 L8 22.5 L8 21.5 L10.5 20 L10 14.5 L2 16 L2 14 L10 11 Z"
              fill="${color}" stroke="#0f172a" stroke-width="0.5" />
      </svg>`,
  });
}

/** Recentres the map when an aircraft is selected from the sidebar. */
function MapController({ target }: { target: [number, number] | null }) {
  const map = useMap();

  useEffect(() => {
    if (target) {
      map.flyTo(target, Math.max(map.getZoom(), 8), { duration: 0.8 });
    }
  }, [target, map]);

  return null;
}

export default function MapView({ aircraft, selectedIcao, onSelect }: MapViewProps) {
  const selectedPosition = useMemo<[number, number] | null>(() => {
    const found = aircraft.find((a) => a.icao24 === selectedIcao);
    return found ? [found.latitude, found.longitude] : null;
  }, [aircraft, selectedIcao]);

  return (
    <MapContainer
      center={SRI_LANKA_CENTER}
      zoom={INITIAL_ZOOM}
      className="h-full w-full bg-slate-900"
      worldCopyJump
    >
            <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={19}
      />

      <MapController target={selectedPosition} />

      {aircraft.map((a) => (
        <Marker
          key={a.icao24}
          position={[a.latitude, a.longitude]}
          icon={createPlaneIcon(a.heading_deg ?? 0, a.icao24 === selectedIcao)}
          eventHandlers={{ click: () => onSelect(a.icao24) }}
        />
      ))}
    </MapContainer>
  );
}