"""
Extra API integration — spec 2.2.
Uses OpenStreetMap Nominatim (free, no key) for place context, and
returns an embeddable OpenStreetMap link (map "API integration" without
requiring a paid Google Maps key — swap-in ready if a key is available).
"""
import httpx

NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


class LocationContextError(Exception):
    pass


async def get_location_context(lat: float, lon: float) -> dict:
    headers = {"User-Agent": "weather-risk-app/1.0 (assessment project)"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                NOMINATIM_REVERSE_URL,
                params={"lat": lat, "lon": lon, "format": "json"},
                headers=headers,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise LocationContextError(f"Location context request failed: {e}")

        data = resp.json()
        address = data.get("address", {})

        return {
            "display_name": data.get("display_name"),
            "city": address.get("city") or address.get("town") or address.get("village"),
            "state": address.get("state"),
            "country": address.get("country"),
            "map_embed_url": f"https://www.openstreetmap.org/#map=13/{lat}/{lon}",
            "static_map_url": (
                f"https://staticmap.openstreetmap.de/staticmap.php?"
                f"center={lat},{lon}&zoom=12&size=500x300&markers={lat},{lon},red-pushpin"
            ),
        }
