"""
Event CRUD + risk-report generation.
This is the differentiator layer sitting on top of weather_routes.py.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models, schemas
from app.services import risk_service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("", response_model=schemas.EventOut, status_code=201)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    wq = db.query(models.WeatherQuery).filter(models.WeatherQuery.id == payload.weather_query_id).first()
    if not wq:
        raise HTTPException(404, "Referenced weather_query_id does not exist")
    if payload.end_time < payload.start_time:
        raise HTTPException(400, "end_time must be on or after start_time")

    event = models.Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=list[schemas.EventOut])
def list_events(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Event).offset(skip).limit(limit).all()


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    return event


@router.put("/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, payload: schemas.EventUpdate, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    db.delete(event)
    db.commit()
    return None


@router.post("/{event_id}/assess-risk", response_model=schemas.RiskReportOut)
def assess_event_risk(event_id: int, db: Session = Depends(get_db)):
    """
    Core differentiator endpoint: scores the event's day against its
    stored weather data and produces a risk report + explanation + checklist.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    wq = event.weather_query
    weather = json.loads(wq.weather_data or "{}")
    forecast = weather.get("forecast", [])

    event_date_str = event.start_time.strftime("%Y-%m-%d")
    day = next((d for d in forecast if d.get("date") == event_date_str), None)
    if not day:
        raise HTTPException(
            422,
            f"No forecast data available for {event_date_str}. "
            "Ensure the linked weather query's date range covers the event date.",
        )

    result = risk_service.score_day(day, event.event_type)

    report = models.RiskReport(
        event_id=event.id,
        heat_risk=result["heat_risk"],
        rain_risk=result["rain_risk"],
        wind_risk=result["wind_risk"],
        overall_risk=result["overall_risk"],
        is_anomalous=0,  # populated by anomaly model in DS project; see README
        top_factors=json.dumps(result["top_factors"]),
        explanation=result["explanation"],
        checklist=json.dumps(result["checklist"]),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{event_id}/risk-reports", response_model=list[schemas.RiskReportOut])
def list_risk_reports(event_id: int, db: Session = Depends(get_db)):
    return db.query(models.RiskReport).filter(models.RiskReport.event_id == event_id).all()
