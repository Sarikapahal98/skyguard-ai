// Every call to the backend goes through here — one place to change the URL,
// one place that mirrors CONTRACT.md's response shapes.

const BASE_URL = "http://localhost:8000";

export async function fetchStationsLive() {
  const res = await fetch(`${BASE_URL}/api/stations/live`);
  if (!res.ok) throw new Error(`stations/live failed: ${res.status}`);
  return res.json(); // { stations: [...] }
}

export async function fetchAlerts() {
  const res = await fetch(`${BASE_URL}/api/alerts`);
  if (!res.ok) throw new Error(`alerts failed: ${res.status}`);
  return res.json(); // { alerts: [...] }
}

// Handy for the "Simulate Sensor Fault" demo button (your Wow Factor).
export async function ingestReading(reading) {
  const res = await fetch(`${BASE_URL}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reading),
  });
  if (!res.ok) throw new Error(`ingest failed: ${res.status}`);
  return res.json();
}