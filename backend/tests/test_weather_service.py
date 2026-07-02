"""
Tests weather_service parsing/validation logic using mocked httpx responses
(no live network needed — sandbox blocks external calls, so this proves
correctness of our code, not Open-Meteo's uptime).
"""
import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import weather_service


def test_geocode_direct_coordinates():
    """'lat,lon' input should short-circuit the API call entirely."""
    async def run():
        result = await weather_service.geocode_location("12.9716, 77.5946")
        assert result["latitude"] == 12.9716
        assert result["longitude"] == 77.5946
        return result

    result = asyncio.run(run())
    print(f"PASS: test_geocode_direct_coordinates -> {result}")


def test_geocode_invalid_coordinates_falls_back_to_text_search():
    """Out-of-range 'lat,lon' shouldn't be treated as coordinates."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [
        {"name": "Testville", "latitude": 1.0, "longitude": 2.0, "country": "Testland"}
    ]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        async def run():
            return await weather_service.geocode_location("999, 999")
        result = asyncio.run(run())
        assert result["name"] == "Testville, Testland"
    print("PASS: test_geocode_invalid_coordinates_falls_back_to_text_search")


def test_geocode_no_results_raises_clean_error():
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        async def run():
            try:
                await weather_service.geocode_location("Nonexistentplacexyz")
                return False
            except weather_service.WeatherServiceError as e:
                assert "Could not find location" in str(e)
                return True
        assert asyncio.run(run())
    print("PASS: test_geocode_no_results_raises_clean_error")


def test_forecast_parsing_shapes_data_correctly():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "daily": {
            "time": ["2026-07-05", "2026-07-06"],
            "temperature_2m_max": [30, 32],
            "temperature_2m_min": [20, 21],
            "precipitation_sum": [0, 5],
            "precipitation_probability_max": [10, 60],
            "windspeed_10m_max": [15, 20],
            "relative_humidity_2m_max": [50, 65],
            "weathercode": [1, 61],
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        async def run():
            return await weather_service.get_forecast(12.9, 77.5, days=2)
        result = asyncio.run(run())
        assert len(result) == 2
        assert result[0]["date"] == "2026-07-05"
        assert result[0]["temp_max"] == 30
        assert result[1]["precipitation_sum"] == 5
    print("PASS: test_forecast_parsing_shapes_data_correctly")


def test_geocoding_http_error_raises_weather_service_error():
    import httpx as httpx_module

    async def raise_error(*args, **kwargs):
        raise httpx_module.ConnectError("simulated network failure")

    with patch("httpx.AsyncClient.get", new=raise_error):
        async def run():
            try:
                await weather_service.geocode_location("SomeCity")
                return False
            except weather_service.WeatherServiceError:
                return True
        assert asyncio.run(run())
    print("PASS: test_geocoding_http_error_raises_weather_service_error")


if __name__ == "__main__":
    test_geocode_direct_coordinates()
    test_geocode_invalid_coordinates_falls_back_to_text_search()
    test_geocode_no_results_raises_clean_error()
    test_forecast_parsing_shapes_data_correctly()
    test_geocoding_http_error_raises_weather_service_error()
    print("\nAll weather_service tests passed.")
