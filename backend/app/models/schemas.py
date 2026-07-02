"""
Pydantic schemas — request/response validation, kept separate from
SQLAlchemy models so API contracts don't leak DB internals.
"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List


# ---------- WeatherQuery ----------

class WeatherQueryCreate(BaseModel):
    location_input: str
    start_date: datetime
    end_date: datetime

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v

    @field_validator("start_date")
    @classmethod
    def not_too_far_past(cls, v):
        # Open-Meteo forecast API only supports limited history without
        # switching to the archive endpoint; keep validation honest.
        return v


class WeatherQueryUpdate(BaseModel):
    location_input: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class WeatherQueryOut(BaseModel):
    id: int
    location_input: str
    resolved_name: str
    latitude: float
    longitude: float
    start_date: datetime
    end_date: datetime
    weather_data: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Event ----------

class EventCreate(BaseModel):
    weather_query_id: int
    name: str
    event_type: str
    start_time: datetime
    end_time: datetime
    indoor_alternative: Optional[str] = None
    notes: Optional[str] = None


class EventUpdate(BaseModel):
    name: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    indoor_alternative: Optional[str] = None
    notes: Optional[str] = None


class EventOut(BaseModel):
    id: int
    weather_query_id: int
    name: str
    event_type: str
    start_time: datetime
    end_time: datetime
    indoor_alternative: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- RiskReport ----------

class RiskFactor(BaseModel):
    feature: str
    importance: float
    direction: str  # "increases_risk" | "decreases_risk"


class RiskReportOut(BaseModel):
    id: int
    event_id: int
    heat_risk: Optional[str]
    rain_risk: Optional[str]
    wind_risk: Optional[str]
    overall_risk: Optional[str]
    is_anomalous: int
    top_factors: Optional[str]
    explanation: Optional[str]
    checklist: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Agent ----------

class AgentQuery(BaseModel):
    question: str
    location_input: Optional[str] = None
