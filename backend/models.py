"""
ORM models — these MUST match the schema in CONTRACT.md exactly.
If you need to add a column, update CONTRACT.md too and tell the team.
"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, TIMESTAMP, ForeignKey, func
from database import Base


class Station(Base):
    __tablename__ = "stations"

    station_id = Column(Integer, primary_key=True, index=True)
    station_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), default="ACTIVE")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    reading_id = Column(BigInteger, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"))
    recorded_at = Column(TIMESTAMP, server_default=func.now())
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    rainfall = Column(Float)
    wind_speed = Column(Float)


class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"

    flag_id = Column(BigInteger, primary_key=True, index=True)
    reading_id = Column(BigInteger, ForeignKey("sensor_readings.reading_id"))
    parameter = Column(String(30), nullable=False)
    anomaly_type = Column(String(30), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    is_severe = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(BigInteger, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"))
    flag_id = Column(BigInteger, ForeignKey("anomaly_flags.flag_id"))
    message = Column(String, nullable=False)
    severity = Column(String(10), nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
