"""
SkyGuard AI — Backend (P2's main file)

Run with:  uvicorn main:app --reload --port 8000

This file wires together: incoming readings -> ML detection -> DB write -> API response.
The ML function is imported from the sibling ml/ folder — P2 does not need to know
how it works internally, only that it matches the contract in CONTRACT.md.
"""
import sys
import os
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import engine, get_db, Base
import models
import schemas

# --- Make the sibling ml/ folder importable ---
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))
from detect import detect_anomaly  # noqa: E402  (P3 owns this function)

# --- Create tables if they don't exist yet (fine for a hackathon MVP) ---
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkyGuard AI Backend")

# Allow the React dev server to call this API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this if you have time; fine for a hackathon
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_or_create_station(db: Session, station_code: str) -> models.Station:
    station = db.query(models.Station).filter_by(station_code=station_code).first()
    if station is None:
        # Auto-create a demo station so the simulator can just start sending data.
        station = models.Station(
            station_code=station_code,
            name=station_code,
            latitude=30.74,
            longitude=76.79,
            status="ACTIVE",
        )
        db.add(station)
        db.commit()
        db.refresh(station)
    return station


def severity_from_score(score: float) -> str:
    if score >= 0.8:
        return "HIGH"
    if score >= 0.5:
        return "MEDIUM"
    return "LOW"


@app.post("/api/ingest", response_model=schemas.IngestResponse)
def ingest_reading(payload: schemas.IngestRequest, db: Session = Depends(get_db)):
    station = get_or_create_station(db, payload.station_code)

    reading = models.SensorReading(
        station_id=station.station_id,
        temperature=payload.temperature,
        humidity=payload.humidity,
        pressure=payload.pressure,
        rainfall=payload.rainfall,
        wind_speed=payload.wind_speed,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # --- Call the ML function (P3's code) ---
    verdict = detect_anomaly(payload.model_dump())

    flag = models.AnomalyFlag(
        reading_id=reading.reading_id,
        parameter=verdict.get("parameter") or "none",
        anomaly_type=verdict["anomaly_type"],
        anomaly_score=verdict["anomaly_score"],
        is_severe=verdict.get("is_severe", False),
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)

    alert_created = False
    if verdict["anomaly_detected"]:
        alert = models.Alert(
            station_id=station.station_id,
            flag_id=flag.flag_id,
            message=f"{verdict['anomaly_type']} detected on {flag.parameter} "
                    f"(score {verdict['anomaly_score']:.2f})",
            severity=severity_from_score(verdict["anomaly_score"]),
        )
        db.add(alert)
        db.commit()
        alert_created = True

        # Update station status so the map/dashboard shows it immediately
        station.status = f"ANOMALY_{alert.severity}"
        db.commit()
    else:
        station.status = "NORMAL"
        db.commit()

    return schemas.IngestResponse(
        reading_id=reading.reading_id,
        status="processed",
        anomaly_detected=verdict["anomaly_detected"],
        anomaly_type=verdict["anomaly_type"],
        anomaly_score=verdict["anomaly_score"],
        alert_created=alert_created,
    )


@app.get("/api/stations/live", response_model=schemas.StationsLiveResponse)
def stations_live(db: Session = Depends(get_db)):
    stations = db.query(models.Station).all()
    result = []
    for s in stations:
        last = (
            db.query(models.SensorReading)
            .filter_by(station_id=s.station_id)
            .order_by(desc(models.SensorReading.recorded_at))
            .first()
        )
        active_alerts = (
            db.query(models.Alert)
            .filter_by(station_id=s.station_id, acknowledged=False)
            .count()
        )
        result.append(
            schemas.StationLive(
                station_id=s.station_id,
                station_code=s.station_code,
                latitude=s.latitude,
                longitude=s.longitude,
                status=s.status,
                last_reading=schemas.LastReading(
                    temperature=last.temperature,
                    humidity=last.humidity,
                    recorded_at=last.recorded_at.isoformat(),
                ) if last else None,
                active_alerts=active_alerts,
            )
        )
    return schemas.StationsLiveResponse(stations=result)


@app.get("/api/alerts", response_model=schemas.AlertsResponse)
def get_alerts(db: Session = Depends(get_db)):
    alerts = (
        db.query(models.Alert, models.Station.station_code)
        .join(models.Station, models.Alert.station_id == models.Station.station_id)
        .order_by(desc(models.Alert.created_at))
        .limit(50)
        .all()
    )
    return schemas.AlertsResponse(
        alerts=[
            schemas.AlertOut(
                alert_id=a.alert_id,
                station_code=code,
                message=a.message,
                severity=a.severity,
                acknowledged=a.acknowledged,
                created_at=a.created_at.isoformat(),
            )
            for a, code in alerts
        ]
    )


@app.get("/")
def root():
    return {"message": "SkyGuard AI backend is running. See /docs for the API."}
