import { useEffect, useState, useCallback } from "react";
import { fetchStationsLive, fetchAlerts, ingestReading } from "./api";

const POLL_INTERVAL_MS = 3000;

const STATUS_LABEL = {
  NORMAL: "Normal",
  ANOMALY_LOW: "Low anomaly",
  ANOMALY_MEDIUM: "Medium anomaly",
  ANOMALY_HIGH: "High anomaly",
};

export default function App() {
  const [stations, setStations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [stationsData, alertsData] = await Promise.all([
        fetchStationsLive(),
        fetchAlerts(),
      ]);
      setStations(stationsData.stations || []);
      setAlerts(alertsData.alerts || []);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  // Demo helper: fires an obviously-faulty reading so you can show the jury
  // detection happening live, without waiting for the simulator's random timing.
  async function simulateFault(type) {
    const base = {
      station_code: "AWS-CHD-001",
      temperature: 28.0,
      humidity: 55.0,
      pressure: 1010.0,
      rainfall: 0.0,
      wind_speed: 8.0,
    };
    if (type === "spike") base.temperature = 62.0;
    if (type === "flatline") base.humidity = 55.0; // send repeatedly to trigger flatline logic
    if (type === "out_of_range") base.pressure = 1400.0;

    try {
      await ingestReading(base);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>SkyGuard AI</h1>
          <p className="subtitle">Live anomaly monitoring for Automatic Weather Stations</p>
        </div>
        <div className="header__meta">
          {lastUpdated && <span>Updated {lastUpdated.toLocaleTimeString()}</span>}
          {error && <span className="error-badge">Backend unreachable</span>}
        </div>
      </header>

      <section className="demo-controls">
        <span className="demo-controls__label">Demo: simulate a fault —</span>
        <button onClick={() => simulateFault("spike")}>Spike</button>
        <button onClick={() => simulateFault("flatline")}>Flatline</button>
        <button onClick={() => simulateFault("out_of_range")}>Out of range</button>
      </section>

      <main className="app__grid">
        <section className="panel">
          <h2>Stations</h2>
          {/* TODO (P1): swap this table for a Leaflet map with color-coded markers */}
          <table className="station-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Status</th>
                <th>Temp</th>
                <th>Humidity</th>
                <th>Last reading</th>
                <th>Active alerts</th>
              </tr>
            </thead>
            <tbody>
              {stations.map((s) => (
                <tr key={s.station_id} className={`row row--${s.status}`}>
                  <td>{s.station_code}</td>
                  <td>{STATUS_LABEL[s.status] || s.status}</td>
                  <td>{s.last_reading?.temperature ?? "—"}</td>
                  <td>{s.last_reading?.humidity ?? "—"}</td>
                  <td>
                    {s.last_reading
                      ? new Date(s.last_reading.recorded_at).toLocaleTimeString()
                      : "no data yet"}
                  </td>
                  <td>{s.active_alerts}</td>
                </tr>
              ))}
              {stations.length === 0 && (
                <tr>
                  <td colSpan={6} className="empty-state">
                    No stations yet — start the simulator (ml/data_simulator.py --live)
                    or click a demo button above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>

        <section className="panel">
          <h2>Alert feed</h2>
          <ul className="alert-feed">
            {alerts.map((a) => (
              <li key={a.alert_id} className={`alert alert--${a.severity}`}>
                <span className="alert__severity">{a.severity}</span>
                <span className="alert__message">{a.message}</span>
                <span className="alert__station">{a.station_code}</span>
                <span className="alert__time">
                  {new Date(a.created_at).toLocaleTimeString()}
                </span>
              </li>
            ))}
            {alerts.length === 0 && <li className="empty-state">No alerts yet.</li>}
          </ul>
        </section>
      </main>
    </div>
  );
}
