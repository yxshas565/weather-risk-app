from fastapi import APIRouter, HTTPException
from app.services import location_context_service

router = APIRouter(prefix="/api/location-context", tags=["location-context"])


@router.get("")
async def location_context(lat: float, lon: float):
    try:
        return await location_context_service.get_location_context(lat, lon)
    except location_context_service.LocationContextError as e:
        raise HTTPException(502, str(e))
