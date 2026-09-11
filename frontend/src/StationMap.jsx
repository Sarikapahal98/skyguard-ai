import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const STATUS_COLOR = {
  NORMAL: "#4c9a6a",
  ANOMALY_LOW: "#d9b04c",
  ANOMALY_MEDIUM: "#dd8a3c",
  ANOMALY_HIGH: "#d1483f",
};

export default function StationMap({ stations }) {
  const center = stations.length
    ? [stations[0].latitude, stations[0].longitude]
    : [22.9734, 78.6569]; // fallback: center of India

    console.log("stations passed to map:", stations);

  return (
    <MapContainer center={center} zoom={5} style={{ height: "400px", width: "100%" }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {stations.map((s) => (
        <CircleMarker
          key={s.station_id}
          center={[s.latitude, s.longitude]}
          radius={10}
          pathOptions={{ color: STATUS_COLOR[s.status] || "#888", fillOpacity: 0.8 }}
        >
          <Popup>{s.station_code}: {s.status}</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}