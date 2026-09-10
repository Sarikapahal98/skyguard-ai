"""
SkyGuard AI — Anomaly Detection (P3 owns this file)

This is THE function the backend calls. Its input/output shape is fixed by
CONTRACT.md — do not change the shape without updating the contract and
telling the team.

Until model.joblib exists (run train_model.py to create it), this falls back
to a simple rule-based check, so P1/P2 can build and demo against it on day 1
without waiting for real model.
"""
import os
import joblib
import numpy as np
import pandas as pd

FEATURES = ["temperature", "humidity", "pressure", "rainfall", "wind_speed"]

# Physically implausible bounds for a plains India AWS station — tune these
# to match whatever region/dataset you're presenting.
BOUNDS = {
    "temperature": (-10, 55),
    "humidity": (0, 100),
    "pressure": (950, 1050),
    "rainfall": (0, 500),
    "wind_speed": (0, 200),
}

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
_model = None
if os.path.exists(_MODEL_PATH):
    _model = joblib.load(_MODEL_PATH)

# Very simple in-memory history for flatline/drift checks (per-process; fine for a hackathon).
# Keyed by parameter name -> list of recent values.
_recent_history: dict[str, list[float]] = {f: [] for f in FEATURES}
_HISTORY_LEN = 10


def _check_bounds(reading: dict) -> tuple[str, float] | None:
    """Rule-based physical bounds check. Returns (parameter, score) if out of range."""
    for param, (lo, hi) in BOUNDS.items():
        value = reading.get(param)
        if value is not None and not (lo <= value <= hi):
            return param, 0.95
    return None


def _check_flatline(reading: dict) -> tuple[str, float] | None:
    """Same value repeated N times in a row = sensor likely stuck."""
    for param in FEATURES:
        value = reading.get(param)
        if value is None:
            continue
        history = _recent_history[param]
        if len(history) >= 4 and all(v == value for v in history[-4:]):
            return param, 0.75
    return None


def _update_history(reading: dict):
    for param in FEATURES:
        value = reading.get(param)
        if value is None:
            continue
        history = _recent_history[param]
        history.append(value)
        if len(history) > _HISTORY_LEN:
            history.pop(0)

_baseline_avg: dict[tuple[str, str], float] = {}
_DRIFT_ALPHA = 0.05
_DRIFT_THRESHOLDS = {
    "temperature": 5.0,
    "humidity": 10.0,
    "pressure": 4.0,
    "rainfall": 2.0,
    "wind_speed": 5.0,
}


def _check_drift(reading: dict) -> tuple[str, float] | None:
    station = reading.get("station_code", "UNKNOWN")
    for param in FEATURES:
        value = reading.get(param)
        if value is None:
            continue
        key = (station, param)
        if key not in _baseline_avg:
            _baseline_avg[key] = value
            continue
        deviation = abs(value - _baseline_avg[key])
        _baseline_avg[key] = (1 - _DRIFT_ALPHA) * _baseline_avg[key] + _DRIFT_ALPHA * value
        threshold = _DRIFT_THRESHOLDS[param]
        if deviation > threshold:
            return param, min(0.6 + deviation / (threshold * 6), 0.9)
    return None


def _model_score(reading: dict) -> float | None:
    """Uses the trained IsolationForest, if available, to get an anomaly score."""
    if _model is None:
        return None
    x = pd.DataFrame(
    [[reading.get(f, 0.0) or 0.0 for f in FEATURES]],
    columns=FEATURES,
    )


    # IsolationForest: decision_function is higher = more normal, so we flip and normalize.
    raw = _model.decision_function(x)[0]
    score = float(np.clip(0.5 - raw, 0.0, 1.0))
    return score


def detect_anomaly(reading: dict) -> dict:
    """
    Input: a single sensor reading, e.g.
        {"temperature": 38.4, "humidity": 62.1, "pressure": 1008.3,
         "rainfall": 0.0, "wind_speed": 12.5}

    Output (fixed shape — see CONTRACT.md):
        {
            "anomaly_detected": bool,
            "anomaly_type": "SPIKE" | "DRIFT" | "FLATLINE" | "OUT_OF_RANGE" | "NONE",
            "anomaly_score": float (0.0-1.0),
            "parameter": str | None,
            "is_severe": bool
        }
    """
    # 1. Rule-based hard bounds check (highest priority — physically impossible values)
    bounds_hit = _check_bounds(reading)
    if bounds_hit:
        param, score = bounds_hit
        _update_history(reading)
        return {
            "anomaly_detected": True,
            "anomaly_type": "OUT_OF_RANGE",
            "anomaly_score": score,
            "parameter": param,
            "is_severe": True,
        }

    # 2. Flatline check (stuck sensor)
    flatline_hit = _check_flatline(reading)
    if flatline_hit:
        param, score = flatline_hit
        _update_history(reading)
        return {
            "anomaly_detected": True,
            "anomaly_type": "FLATLINE",
            "anomaly_score": score,
            "parameter": param,
            "is_severe": False,
        }

    # 3. Drift check (slow, consistent movement away from baseline)
    drift_hit = _check_drift(reading)
    if drift_hit:
        param, score = drift_hit
        _update_history(reading)
        return {
            "anomaly_detected": True,
            "anomaly_type": "DRIFT",
            "anomaly_score": score,
            "parameter": param,
            "is_severe": score >= 0.8,
        }


    # 4. ML model score (catches spikes/drift the rules above don't)
    model_score = _model_score(reading)
    _update_history(reading)

    if model_score is not None and model_score >= 0.5:
        return {
            "anomaly_detected": True,
            "anomaly_type": "SPIKE",
            "anomaly_score": model_score,
            "parameter": "temperature",  # simplification: refine to report the actual driver feature
            "is_severe": model_score >= 0.8,
        }

    # 5. Nothing unusual
    return {
        "anomaly_detected": False,
        "anomaly_type": "NONE",
        "anomaly_score": model_score if model_score is not None else 0.05,
        "parameter": None,
        "is_severe": False,
    }


if __name__ == "__main__":
    # Quick manual test
    sample = {"temperature": 60.0, "humidity": 55.0, "pressure": 1010.0, "rainfall": 0.0, "wind_speed": 8.0}
    print(detect_anomaly(sample))
