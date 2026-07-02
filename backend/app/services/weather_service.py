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
        try:
            resp = await client.get(GEOCODE_URL, params={"name": query, "count": 1})
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise WeatherServiceError(f"Geocoding request failed: {e}")

        data = resp.json()
        results = data.get("results")
        if not results:
            raise WeatherServiceError(
                f"Could not find location matching '{query}'. "
                "Try a city name, postal code, or 'lat,lon' coordinates."
            )

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


async def get_forecast(lat: float, lon: float, days: int = 5) -> list[dict]:
    """Returns daily forecast list, spec requires at minimum 5-day (1.1)."""
    days = max(1, min(days, 16))  # Open-Meteo daily forecast supports up to 16
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(FORECAST_URL, params={
                "latitude": lat,
                "longitude": lon,
                "daily": ",".join(DAILY_FIELDS),
                "forecast_days": days,
                "timezone": "auto",
            })
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise WeatherServiceError(f"Forecast request failed: {e}")

        daily = resp.json().get("daily", {})
        if not daily:
            return []

        dates = daily.get("time", [])
        return [
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


async def get_weather_for_range(lat: float, lon: float, start_date, end_date) -> dict:
    """
    Fetches current + forecast and packages for storage against a
    WeatherQuery record (spec 2.1 CREATE).
    """
    current = await get_current_weather(lat, lon)
    forecast_days = max(1, (end_date - start_date).days + 1)
    forecast = await get_forecast(lat, lon, days=forecast_days)
    return {"current": current, "forecast": forecast}
