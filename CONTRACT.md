# SkyGuard AI — Team Contract
### Read this together as a team BEFORE writing feature code. This is the agreement between Frontend, Backend, and ML. Do not change these shapes without telling the other two people.

---

## 1. Database Schema (P2 owns creating these tables)

```sql
CREATE TABLE stations (
    station_id      SERIAL PRIMARY KEY,
    station_code    VARCHAR(20) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    status          VARCHAR(20) DEFAULT 'ACTIVE'
);

CREATE TABLE sensor_readings (
    reading_id      BIGSERIAL PRIMARY KEY,
    station_id      INTEGER REFERENCES stations(station_id),
    recorded_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    temperature     DOUBLE PRECISION,
    humidity        DOUBLE PRECISION,
    pressure        DOUBLE PRECISION,
    rainfall        DOUBLE PRECISION,
    wind_speed      DOUBLE PRECISION
);

CREATE TABLE anomaly_flags (
    flag_id         BIGSERIAL PRIMARY KEY,
    reading_id      BIGINT REFERENCES sensor_readings(reading_id),
    parameter       VARCHAR(30) NOT NULL,
    anomaly_type    VARCHAR(30) NOT NULL,   -- 'SPIKE','DRIFT','FLATLINE','OUT_OF_RANGE','NONE'
    anomaly_score   DOUBLE PRECISION NOT NULL,
    is_severe       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alerts (
    alert_id        BIGSERIAL PRIMARY KEY,
    station_id      INTEGER REFERENCES stations(station_id),
    flag_id         BIGINT REFERENCES anomaly_flags(flag_id),
    message         TEXT NOT NULL,
    severity        VARCHAR(10) NOT NULL,   -- 'LOW','MEDIUM','HIGH'
    acknowledged    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 2. The ML Contract (P3 must match this exactly — this is what Backend calls)

P3 delivers a single Python function backend imports directly. No HTTP call needed between backend and ML — they run in the same process for simplicity.

```python
# ml/detect.py
def detect_anomaly(reading: dict) -> dict:
    """
    Input (from backend, one sensor reading):
        {
            "temperature": 38.4,
            "humidity": 62.1,
            "pressure": 1008.3,
            "rainfall": 0.0,
            "wind_speed": 12.5
        }

    Output (MUST match this shape exactly):
        {
            "anomaly_detected": true,
            "anomaly_type": "SPIKE",       # one of: SPIKE, DRIFT, FLATLINE, OUT_OF_RANGE, NONE
            "anomaly_score": 0.87,          # float between 0.0 and 1.0
            "parameter": "temperature",     # which field triggered it (or null if none)
            "is_severe": true
        }
    """
```

Until P3's real model is ready, this function can return **hardcoded fake values** so P1 and P2 can build against it immediately (see `ml/detect.py` stub already in this repo).

---

## 3. API Endpoints (P2 owns implementing these — P1 builds against this exactly)

### POST `/api/ingest`
Frontend/simulator sends a raw sensor reading. Backend saves it, calls ML, saves the verdict, returns the combined result.

**Request body:**
```json
{
  "station_code": "AWS-CHD-001",
  "temperature": 38.4,
  "humidity": 62.1,
  "pressure": 1008.3,
  "rainfall": 0.0,
  "wind_speed": 12.5
}
```

**Response body:**
```json
{
  "reading_id": 10432,
  "status": "processed",
  "anomaly_detected": true,
  "anomaly_type": "SPIKE",
  "anomaly_score": 0.87,
  "alert_created": true
}
```

---

### GET `/api/stations/live`
Frontend polls this (every few seconds) to render the dashboard.

**Response body:**
```json
{
  "stations": [
    {
      "station_id": 1,
      "station_code": "AWS-CHD-001",
      "latitude": 30.74,
      "longitude": 76.79,
      "status": "ANOMALY_HIGH",
      "last_reading": {
        "temperature": 38.4,
        "humidity": 62.1,
        "recorded_at": "2026-08-31T10:15:00"
      },
      "active_alerts": 1
    }
  ]
}
```
`status` is one of: `NORMAL`, `ANOMALY_LOW`, `ANOMALY_MEDIUM`, `ANOMALY_HIGH`.

---

### GET `/api/alerts`
**Response body:**
```json
{
  "alerts": [
    {
      "alert_id": 88,
      "station_code": "AWS-CHD-001",
      "message": "Temperature spike detected: 38.4°C",
      "severity": "HIGH",
      "acknowledged": false,
      "created_at": "2026-08-31T10:15:03"
    }
  ]
}
```

---

## 4. Rules Everyone Agreed To

1. Field names are `snake_case` everywhere (`station_code`, not `stationCode`). No exceptions, on either side.
2. Timestamps are always ISO 8601 strings (`"2026-08-31T10:15:00"`).
3. `anomaly_score` is always a float from 0.0 to 1.0, never a raw/unbounded number.
4. If you need to change any shape above, message the group chat first — don't silently change it in your own folder.
5. Backend URL during development: `http://localhost:8000`. Frontend calls this directly (CORS is enabled in the backend skeleton already).