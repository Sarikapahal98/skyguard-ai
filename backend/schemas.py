"""
Pydantic schemas — these define the exact JSON shapes from CONTRACT.md.
Frontend (P1) should treat these as the source of truth for what to send/expect.
"""
from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    station_code: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    rainfall: Optional[float] = None
    wind_speed: Optional[float] = None


class IngestResponse(BaseModel):
    reading_id: int
    status: str
    anomaly_detected: bool
    anomaly_type: str
    anomaly_score: float
    alert_created: bool


class LastReading(BaseModel):
    temperature: Optional[float]
    humidity: Optional[float]
    recorded_at: str


class StationLive(BaseModel):
    station_id: int
    station_code: str
    latitude: float
    longitude: float
    status: str
    last_reading: Optional[LastReading]
    active_alerts: int


class StationsLiveResponse(BaseModel):
    stations: list[StationLive]


class AlertOut(BaseModel):
    alert_id: int
    station_code: str
    message: str
    severity: str
    acknowledged: bool
    created_at: str

class AlertsResponse(BaseModel):
    alerts: list[AlertOut]