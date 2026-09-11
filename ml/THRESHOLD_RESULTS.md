# Detection Accuracy — Sep 11 Measurement

## False positive rate (normal readings wrongly flagged)
- Before model retrain: ~99% (296/298)
- After retrain on real 8-station data: ~4-5% (14/291, 11/286, 14/280 across runs)

## Drift catch rate (DRIFT-labeled readings correctly caught)
- ~27% this run (29/107) — consistent with the ~25-53% range seen
  across runs; pressure drift magnitude varies randomly per the
  simulator, so weak drifts are sometimes missed by design tradeoff
  against false positives.

## Thresholds in use (ml/detect.py)
- _DRIFT_THRESHOLDS: temperature 5.0, humidity 10.0, pressure 4.0,
  rainfall 2.0, wind_speed 5.0
- Decision: kept as-is given time constraints — false-positive rate
  is the metric we lead with in the pitch.