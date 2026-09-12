"""
SkyGuard AI — Synthetic AWS Data Generator (P3)

Generates realistic-looking weather station readings and injects
three types of sensor faults:

    SPIKE
    FLATLINE
    DRIFT

The generate_dataset() function and "label" field must remain
compatible with the rest of the SkyGuard AI project.
"""

import argparse
import random
import time
import requests
import random


STATIONS = [
    {"code": "AWS-CHN-01", "lat": 13.00, "lon": 80.18, "baseline": {"temperature": 28.5, "humidity": 70, "pressure": 1010, "rainfall": 3.6, "wind_speed": 10}},
    {"code": "AWS-AMD-01", "lat": 23.03, "lon": 72.58, "baseline": {"temperature": 27.7, "humidity": 45, "pressure": 1008, "rainfall": 2.2, "wind_speed": 9}},
    {"code": "AWS-BLR-01", "lat": 12.97, "lon": 77.59, "baseline": {"temperature": 23.8, "humidity": 60, "pressure": 1013, "rainfall": 2.6, "wind_speed": 7}},
    {"code": "AWS-CHD-01", "lat": 30.74, "lon": 76.79, "baseline": {"temperature": 23.5, "humidity": 55, "pressure": 1010, "rainfall": 2.9, "wind_speed": 8}},
    {"code": "AWS-DEH-01", "lat": 30.32, "lon": 78.03, "baseline": {"temperature": 21.6, "humidity": 65, "pressure": 1009, "rainfall": 6.1, "wind_speed": 6}},
    {"code": "AWS-BHO-01", "lat": 23.26, "lon": 77.41, "baseline": {"temperature": 25.2, "humidity": 50, "pressure": 1011, "rainfall": 3.1, "wind_speed": 8}},
    {"code": "AWS-CHP-01", "lat": 25.30, "lon": 91.70, "baseline": {"temperature": 17.3, "humidity": 90, "pressure": 1012, "rainfall": 30.7, "wind_speed": 12}},
    {"code": "AWS-BIK-01", "lat": 28.02, "lon": 73.31, "baseline": {"temperature": 26.5, "humidity": 30, "pressure": 1007, "rainfall": 0.9, "wind_speed": 11}},
]
import os
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000") + "/api/ingest"

_last_reading = dict(STATIONS[0]["baseline"])
def normal_reading():
    station = random.choice(STATIONS)
    b = station["baseline"]
    return {
        "station_code": station["code"],
        "latitude": station["lat"],
        "longitude": station["lon"],
        "temperature": round(b["temperature"] + random.uniform(-2, 2), 1),
        "humidity": round(b["humidity"] + random.uniform(-5, 5), 1),
        "pressure": round(b["pressure"] + random.uniform(-1.5, 1.5), 1),
        "rainfall": round(max(0, b["rainfall"] + random.uniform(-0.5, 1.0)), 1),
        "wind_speed": round(b["wind_speed"] + random.uniform(-2, 2), 1),
    }


def inject_spike(reading: dict) -> dict:
    """
    Inject a sudden but variable sensor spike.

    The spike magnitude is randomly selected so that every
    SPIKE is not exactly the same.
    """

    reading = dict(reading)

    # Variable temperature spike.
    # Most spikes are significant but not identical.
    spike = random.uniform(8, 18)

    reading["temperature"] = round(
        reading["temperature"] + spike,
        1
    )

    return reading


def inject_flatline(reading: dict) -> dict:
    """
    Start a flatline fault.

    The sensor becomes stuck at its previous value.
    The duration of the flatline is controlled by
    generate_dataset(), which produces 3-8 consecutive
    FLATLINE readings.
    """

    global _last_reading

    reading = dict(reading)

    # Humidity sensor gets stuck at its previous value.
    reading["humidity"] = _last_reading["humidity"]

    return reading


def inject_drift(reading: dict, step: int) -> dict:
    """
    Inject gradual pressure sensor drift.

    Drift grows gradually but includes random variation,
    so it does not form a perfectly straight line.
    """

    reading = dict(reading)

    # Small random amount of drift for this reading.
    drift_increment = random.uniform(0.3, 0.8)

    # Small noise prevents perfectly linear movement.
    noise = random.uniform(-0.15, 0.15)

    drift = (step * drift_increment) + noise

    reading["pressure"] = round(
        reading["pressure"] + drift,
        1
    )

    return reading


def generate_dataset(
    n: int = 2000,
    fault_rate: float = 0.05
) -> list[dict]:
    """
    Generate a labeled synthetic AWS dataset.

    Labels:
        NONE
        SPIKE
        FLATLINE
        DRIFT

    Approximately fault_rate of the readings are faulty.
    """

    global _last_reading

    data = []

    i = 0

    while i < n:

        reading = normal_reading()
        label = "NONE"

        roll = random.random()

        # -------------------------------------------------
        # SPIKE
        # -------------------------------------------------
        if roll < fault_rate / 3:

            reading = inject_spike(reading)
            reading["label"] = "SPIKE"

            data.append(reading)
            _last_reading = reading

            i += 1

        # -------------------------------------------------
        # FLATLINE
        # -------------------------------------------------
        elif roll < 2 * fault_rate / 3:

            # Random duration between 3 and 8 readings.
            duration = random.randint(3, 8)

            # Do not exceed requested dataset size.
            duration = min(duration, n - i)

            # The sensor gets stuck at one value.
            stuck_value = reading["humidity"]

            for _ in range(duration):

                flatline_reading = normal_reading()

                # Keep humidity exactly the same.
                flatline_reading["humidity"] = stuck_value

                flatline_reading["label"] = "FLATLINE"

                data.append(flatline_reading)

                _last_reading = flatline_reading

                i += 1

        # -------------------------------------------------
        # DRIFT
        # -------------------------------------------------
        elif roll < fault_rate:

            # Random duration of the drifting fault.
            duration = random.randint(4, 8)

            duration = min(duration, n - i)

            # Start from a realistic pressure value.
            starting_pressure = reading["pressure"]

            # Random direction.
            direction = random.choice([-1, 1])

            # Small drift amount per reading.
            drift_step = random.uniform(0.3, 0.7)

            for drift_index in range(duration):

                drift_reading = normal_reading()

                # Random noise makes the drift less perfectly linear.
                noise = random.uniform(-0.15, 0.15)

                drift_amount = (
                    drift_index * drift_step
                    + noise
                )

                drift_reading["pressure"] = round(
                    starting_pressure
                    + direction * drift_amount,
                    1
                )

                drift_reading["label"] = "DRIFT"

                data.append(drift_reading)

                _last_reading = drift_reading

                i += 1

        # -------------------------------------------------
        # NORMAL
        # -------------------------------------------------
        else:

            reading["label"] = "NONE"

            data.append(reading)

            _last_reading = reading

            i += 1

    return data


def run_live_feed(
    interval_seconds: float = 3.0,
    fault_rate: float = 0.1
):
    """
    Continuously POST synthetic readings to the backend.
    """

    print(
        f"Streaming synthetic readings to {BACKEND_URL} "
        f"every {interval_seconds}s..."
    )

    step = 0

    while True:

        reading = normal_reading()

        roll = random.random()

        if roll < fault_rate / 3:

            reading = inject_spike(reading)

        elif roll < 2 * fault_rate / 3:

            reading = inject_flatline(reading)

        elif roll < fault_rate:

            reading = inject_drift(
                reading,
                step=step
            )

        try:

            resp = requests.post(
                BACKEND_URL,
                json=reading,
                timeout=5
            )

            print(
                step,
                reading,
                "->",
                resp.status_code,
                resp.json()
            )

        except requests.exceptions.RequestException as e:

            print(
                "Could not reach backend "
                "(is it running?):",
                e
            )

        step += 1

        time.sleep(interval_seconds)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--live",
        action="store_true",
        help="Stream readings to the backend"
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=3.0
    )

    args = parser.parse_args()

    if args.live:

        run_live_feed(
            interval_seconds=args.interval
        )

    else:

        preview = generate_dataset(n=10)

        for row in preview:
            print(row)