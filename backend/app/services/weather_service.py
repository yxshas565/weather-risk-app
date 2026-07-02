"""
Weather data service — wraps Open-Meteo (free, no API key required).

Two Open-Meteo endpoints used:
  1. Geocoding API — resolves free-text location input (city, landmark, etc.)
     to lat/lon. Handles spec requirement: "zip/coords/landmark/town/city"
     input flexibility via fuzzy text search.
  2. Forecast API — current conditions + up to 16-day daily forecast.

Raises WeatherServiceError on failure so routes can return clean 4xx/5xx
with real messages (spec 1.2 error handling).
"""
import httpx
from typing import Optional

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_FIELDS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "windspeed_10m_max",
    "relative_humidity_2m_max",
    "weathercode",
]

CURRENT_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "weathercode",
    "windspeed_10m",
]


class WeatherServiceError(Exception):
    pass


async def geocode_location(query: str) -> dict:
    """
    Resolves free-text location input to lat/lon + display name.
    Supports fuzzy matching per spec 2.1 ("allow fuzzy match for system
    to determine location"). Also handles raw "lat,lon" input directly.
    """
    query = query.strip()

    # Direct GPS coordinate input: "12.9716,77.5946"
    if "," in query:
        parts = query.split(",")
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0].strip()), float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return {
                        "name": f"{lat:.4f}, {lon:.4f}",
                        "latitude": lat,
                        "longitude": lon,
                    }
            except ValueError:
                pass  # fall through to text geocoding

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Try Open-Meteo first — fast, good for city/town names
        try:
            resp = await client.get(GEOCODE_URL, params={"name": query, "count": 1})
            resp.raise_for_status()
            results = resp.json().get("results")
        except httpx.HTTPError:
            results = None

        if results:
            top = results[0]
            display_parts = [top.get("name")]
            if top.get("admin1"):
                display_parts.append(top["admin1"])
            if top.get("country"):
                display_parts.append(top["country"])
            return {
                "name": ", ".join(p for p in display_parts if p),
                "latitude": top["latitude"],
                "longitude": top["longitude"],
            }

        # Fallback: Nominatim — handles postal codes, street addresses,
        # landmarks that Open-Meteo's gazetteer misses.
        try:
            resp = await client.get(
                NOMINATIM_URL,
                params={"q": query, "format": "json", "limit": 1, "addressdetails": 1},
                headers={"User-Agent": "weather-risk-assistant/1.0"},
            )
            resp.raise_for_status()
            nom_results = resp.json()
        except httpx.HTTPError as e:
            raise WeatherServiceError(f"Geocoding request failed: {e}")

        if not nom_results:
            raise WeatherServiceError(
                f"Could not find location matching '{query}'. "
                "Try a city name, postal code, landmark, or 'lat,lon' coordinates."
            )

        top = nom_results[0]
        return {
            "name": top.get("display_name", query),
            "latitude": float(top["lat"]),
            "longitude": float(top["lon"]),
        }


async def get_current_weather(lat: float, lon: float) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(FORECAST_URL, params={
                "latitude": lat,
                "longitude": lon,
                "current": ",".join(CURRENT_FIELDS),
                "timezone": "auto",
            })
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise WeatherServiceError(f"Current weather request failed: {e}")
        return resp.json().get("current", {})


async def get_forecast(lat: float, lon: float, days: int = 5, start_date=None, end_date=None) -> list[dict]:
    """
    Returns daily forecast list. Open-Meteo's forecast_days param always
    starts from today, so when a specific future start_date is requested,
    we fetch enough days to cover it, then slice to the exact window.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        if start_date and end_date:
            from datetime import date
            today = date.today()
            target_end = end_date.date() if hasattr(end_date, "date") else end_date
            days_needed = max(1, (target_end - today).days + 1)
            days_needed = min(days_needed, 16)
        else:
            days_needed = max(1, min(days, 16))

        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(DAILY_FIELDS),
            "timezone": "auto",
            "forecast_days": days_needed,
        }

        try:
            resp = await client.get(FORECAST_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise WeatherServiceError(f"Forecast request failed: {e}")

        daily = resp.json().get("daily", {})
        if not daily:
            return []

        dates = daily.get("time", [])
        rows = [
            {
                "date": dates[i],
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "precipitation_sum": daily["precipitation_sum"][i],
                "precipitation_probability": daily["precipitation_probability_max"][i],
                "windspeed_max": daily["windspeed_10m_max"][i],
                "humidity_max": daily["relative_humidity_2m_max"][i],
                "weathercode": daily["weathercode"][i],
            }
            for i in range(len(dates))
        ]

        if start_date and end_date:
            start_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
            end_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)
            rows = [r for r in rows if start_str <= r["date"] <= end_str]

        return rows

async def get_weather_for_range(lat: float, lon: float, start_date, end_date) -> dict:
    """
    Fetches current + forecast and packages for storage against a
    WeatherQuery record (spec 2.1 CREATE).
    """
    current = await get_current_weather(lat, lon)
    forecast = await get_forecast(lat, lon, start_date=start_date, end_date=end_date)
    return {"current": current, "forecast": forecast}
