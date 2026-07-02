"""
Weather query CRUD routes — satisfies spec 2.1 in full:
  CREATE - location + date range -> fetch & store weather, with validation
  READ   - list/get stored queries (no row-level security per spec note)
  UPDATE - modify stored query fields
  DELETE - remove a stored query
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models, schemas
from app.services import weather_service, export_service

router = APIRouter(prefix="/api/weather-queries", tags=["weather-queries"])

MAX_RANGE_DAYS = 16  # Open-Meteo forecast limit


@router.post("", response_model=schemas.WeatherQueryOut, status_code=201)
async def create_weather_query(payload: schemas.WeatherQueryCreate, db: Session = Depends(get_db)):
    # Validate date range length
    range_days = (payload.end_date - payload.start_date).days + 1
    if range_days < 1:
        raise HTTPException(400, "end_date must be on or after start_date")
    if range_days > MAX_RANGE_DAYS:
        raise HTTPException(
            400,
            f"Date range too long ({range_days} days). "
            f"Free forecast API supports up to {MAX_RANGE_DAYS} days.",
        )

    # Validate location exists (fuzzy match handled inside geocode_location)
    try:
        location = await weather_service.geocode_location(payload.location_input)
    except weather_service.WeatherServiceError as e:
        raise HTTPException(422, str(e))

    try:
        weather_data = await weather_service.get_weather_for_range(
            location["latitude"], location["longitude"],
            payload.start_date, payload.end_date,
        )
    except weather_service.WeatherServiceError as e:
        raise HTTPException(502, f"Weather provider error: {e}")

    record = models.WeatherQuery(
        location_input=payload.location_input,
        resolved_name=location["name"],
        latitude=location["latitude"],
        longitude=location["longitude"],
        start_date=payload.start_date,
        end_date=payload.end_date,
        weather_data=json.dumps(weather_data, default=str),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[schemas.WeatherQueryOut])
def list_weather_queries(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.WeatherQuery).offset(skip).limit(limit).all()


@router.get("/{query_id}", response_model=schemas.WeatherQueryOut)
def get_weather_query(query_id: int, db: Session = Depends(get_db)):
    record = db.query(models.WeatherQuery).filter(models.WeatherQuery.id == query_id).first()
    if not record:
        raise HTTPException(404, "Weather query not found")
    return record


@router.put("/{query_id}", response_model=schemas.WeatherQueryOut)
async def update_weather_query(query_id: int, payload: schemas.WeatherQueryUpdate, db: Session = Depends(get_db)):
    record = db.query(models.WeatherQuery).filter(models.WeatherQuery.id == query_id).first()
    if not record:
        raise HTTPException(404, "Weather query not found")

    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(400, "end_date must be on or after start_date")

    # If location changed, re-geocode and re-fetch to keep data coherent
    location_changed = payload.location_input and payload.location_input != record.location_input
    if location_changed:
        try:
            location = await weather_service.geocode_location(payload.location_input)
            record.location_input = payload.location_input
            record.resolved_name = location["name"]
            record.latitude = location["latitude"]
            record.longitude = location["longitude"]
        except weather_service.WeatherServiceError as e:
            raise HTTPException(422, str(e))

    if payload.start_date:
        record.start_date = payload.start_date
    if payload.end_date:
        record.end_date = payload.end_date

    if location_changed or payload.start_date or payload.end_date:
        try:
            weather_data = await weather_service.get_weather_for_range(
                record.latitude, record.longitude, record.start_date, record.end_date,
            )
            record.weather_data = json.dumps(weather_data, default=str)
        except weather_service.WeatherServiceError as e:
            raise HTTPException(502, f"Weather provider error: {e}")

    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{query_id}", status_code=204)
def delete_weather_query(query_id: int, db: Session = Depends(get_db)):
    record = db.query(models.WeatherQuery).filter(models.WeatherQuery.id == query_id).first()
    if not record:
        raise HTTPException(404, "Weather query not found")
    db.delete(record)
    db.commit()
    return None


@router.get("/{query_id}/export")
def export_weather_query(query_id: int, format: str = "json", db: Session = Depends(get_db)):
    """Spec 2.3 — export in JSON, CSV, XML, PDF, or Markdown."""
    from fastapi.responses import Response, PlainTextResponse

    record = db.query(models.WeatherQuery).filter(models.WeatherQuery.id == query_id).first()
    if not record:
        raise HTTPException(404, "Weather query not found")

    weather = json.loads(record.weather_data or "{}")
    rows = weather.get("forecast", [])
    for row in rows:
        row["location"] = record.resolved_name

    fmt = format.lower()
    if fmt == "json":
        return PlainTextResponse(export_service.to_json(rows), media_type="application/json")
    elif fmt == "csv":
        return PlainTextResponse(export_service.to_csv(rows), media_type="text/csv")
    elif fmt == "xml":
        return PlainTextResponse(export_service.to_xml(rows), media_type="application/xml")
    elif fmt == "markdown":
        return PlainTextResponse(export_service.to_markdown(rows), media_type="text/markdown")
    elif fmt == "pdf":
        pdf_bytes = export_service.to_pdf_bytes(rows, title=f"Weather Export — {record.resolved_name}")
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=weather_{query_id}.pdf"},
        )
    else:
        raise HTTPException(400, f"Unsupported format '{format}'. Use json, csv, xml, markdown, or pdf.")
