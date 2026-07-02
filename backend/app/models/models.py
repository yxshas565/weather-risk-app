"""
Core data models.

Design note: the spec asks for CRUD over "location + date range -> weather".
We satisfy that literally via WeatherQuery, and layer Event + RiskReport on
top for the risk-assistant differentiator. Nothing required by the spec is
replaced — WeatherQuery alone would fully satisfy section 2.1.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class WeatherQuery(Base):
    """
    Satisfies spec 2.1 CRUD: user enters location + date range, we store
    the resolved location and the weather data retrieved for that range.
    """
    __tablename__ = "weather_queries"

    id = Column(Integer, primary_key=True, index=True)
    location_input = Column(String, nullable=False)       # raw user input
    resolved_name = Column(String, nullable=False)         # geocoded display name
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    weather_data = Column(Text, nullable=True)              # JSON-serialized forecast
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("Event", back_populates="weather_query", cascade="all, delete-orphan")


class Event(Base):
    """
    An event or shift the user wants risk-assessed. This is the
    "decision" layer sitting on top of raw weather.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    weather_query_id = Column(Integer, ForeignKey("weather_queries.id"), nullable=False)
    name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)   # e.g. "outdoor_event", "construction_shift", "sports"
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    indoor_alternative = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    weather_query = relationship("WeatherQuery", back_populates="events")
    risk_reports = relationship("RiskReport", back_populates="event", cascade="all, delete-orphan")


class RiskReport(Base):
    """
    Output of the risk-scoring + explainability layer for a given event.
    """
    __tablename__ = "risk_reports"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    heat_risk = Column(String, nullable=True)       # Low / Medium / High
    rain_risk = Column(String, nullable=True)
    wind_risk = Column(String, nullable=True)
    overall_risk = Column(String, nullable=True)
    is_anomalous = Column(Integer, default=0)        # 0/1 flag from anomaly detection
    top_factors = Column(Text, nullable=True)         # JSON list of {feature, importance}
    explanation = Column(Text, nullable=True)          # natural-language explanation
    checklist = Column(Text, nullable=True)            # JSON list of recommended actions
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="risk_reports")
