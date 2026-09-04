"""
SkyGuard AI — Synthetic AWS Data Generator (P3's starting point)

Generates realistic-looking weather station readings, with the option to inject
faults (spike, drift, flatline) so you have labeled data to test your anomaly
detector against, and so P1/P2 can demo "live" data without real hardware.

Run standalone to preview data:
    python data_simulator.py

Run as a live feed that POSTs to the backend (once P2's /api/ingest is up):
    python data_simulator.py --live
"""
import argparse
import random
import time
import requests

STATION_CODE = "AWS-CHD-001"
BACKEND_URL = "http://localhost:8000/api/ingest"

# Roughly realistic baselines for a plains station in India
BASELINE = {
    "temperature": 28.0,   # deg C
    "humidity": 55.0,      # %
    "pressure": 1010.0,    # hPa
    "rainfall": 0.0,       # mm
    "wind_speed": 8.0,     # km/h
}

_last_reading = dict(BASELINE)  # used to simulate drift/flatline over time


def normal_reading() -> dict:
    """A plausible reading with small random noise around the baseline."""
    return {
        "station_code": STATION_CODE,
        "temperature": round(BASELINE["temperature"] + random.uniform(-2, 2), 1),
        "humidity": round(BASELINE["humidity"] + random.uniform(-5, 5), 1),
        "pressure": round(BASELINE["pressure"] + random.uniform(-1.5, 1.5), 1),
        "rainfall": round(max(0, random.uniform(-0.2, 0.5)), 1),
        "wind_speed": round(BASELINE["wind_speed"] + random.uniform(-2, 2), 1),
    }


def inject_spike(reading: dict) -> dict:
    """A sudden, physically implausible jump in one parameter."""
    reading = dict(reading)
    reading["temperature"] = round(reading["temperature"] + random.uniform(15, 25), 1)
    return reading


def inject_flatline(reading: dict) -> dict:
    """Sensor stuck repeating the exact same value (a classic hardware fault)."""
    global _last_reading
    reading = dict(reading)
    reading["humidity"] = _last_reading["humidity"]
    return reading


def inject_drift(reading: dict, step: int) -> dict:
    """Sensor slowly drifting away from reality over many readings."""
    reading = dict(reading)
    reading["pressure"] = round(reading["pressure"] + step * 0.8, 1)
    return reading


def generate_dataset(n: int = 2000, fault_rate: float = 0.05) -> list[dict]:
    """Generate a labeled synthetic dataset for training/testing the model."""
    global _last_reading
    data = []
    for i in range(n):
        reading = normal_reading()
        label = "NONE"

        roll = random.random()
        if roll < fault_rate / 3:
            reading = inject_spike(reading)
            label = "SPIKE"
        elif roll < 2 * fault_rate / 3:
            reading = inject_flatline(reading)
            label = "FLATLINE"
        elif roll < fault_rate:
            reading = inject_drift(reading, step=i % 50)
            label = "DRIFT"

        reading["label"] = label
        data.append(reading)
        _last_reading = reading

    return data


def run_live_feed(interval_seconds: float = 3.0, fault_rate: float = 0.1):
    """Continuously POST readings to the backend — this is your 'live AWS feed' for the demo."""
    print(f"Streaming synthetic readings to {BACKEND_URL} every {interval_seconds}s...")
    step = 0
    while True:
        reading = normal_reading()
        roll = random.random()
        if roll < fault_rate / 3:
            reading = inject_spike(reading)
        elif roll < 2 * fault_rate / 3:
            reading = inject_flatline(reading)
        elif roll < fault_rate:
            reading = inject_drift(reading, step=step)

        try:
            resp = requests.post(BACKEND_URL, json=reading, timeout=5)
            print(step, reading, "->", resp.status_code, resp.json())
        except requests.exceptions.RequestException as e:
            print("Could not reach backend (is it running?):", e)

        step += 1
        time.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Stream readings to the backend")
    parser.add_argument("--interval", type=float, default=3.0)
    args = parser.parse_args()

    if args.live:
        run_live_feed(interval_seconds=args.interval)
    else:
        preview = generate_dataset(n=10)
        for row in preview:
            print(row)
