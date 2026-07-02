"""
Integration tests hitting the FastAPI app directly via TestClient,
with weather_service mocked so no live network is required.
Uses an isolated in-memory SQLite DB so it doesn't touch weather_risk.db.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///./test_weather_risk.db"

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

MOCK_LOCATION = {"name": "Bengaluru, Karnataka, India", "latitude": 12.9716, "longitude": 77.5946}
MOCK_WEATHER_DATA = {
    "current": {"temperature_2m": 26, "relative_humidity_2m": 60, "precipitation": 0,
                "weathercode": 1, "windspeed_10m": 12},
    "forecast": [
        {"date": "2026-07-05", "temp_max": 30, "temp_min": 21, "precipitation_sum": 0,
         "precipitation_probability": 10, "windspeed_max": 15, "humidity_max": 55, "weathercode": 1},
        {"date": "2026-07-06", "temp_max": 41, "temp_min": 25, "precipitation_sum": 2,
         "precipitation_probability": 20, "windspeed_max": 18, "humidity_max": 50, "weathercode": 1},
    ],
}


def test_create_weather_query():
    with patch("app.routes.weather_routes.weather_service.geocode_location", new=AsyncMock(return_value=MOCK_LOCATION)), \
         patch("app.routes.weather_routes.weather_service.get_weather_for_range", new=AsyncMock(return_value=MOCK_WEATHER_DATA)):

        resp = client.post("/api/weather-queries", json={
            "location_input": "Bengaluru",
            "start_date": "2026-07-05T00:00:00",
            "end_date": "2026-07-06T00:00:00",
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["resolved_name"] == "Bengaluru, Karnataka, India"
        assert data["id"] > 0
        print(f"PASS: test_create_weather_query -> id={data['id']}")
        return data["id"]


def test_read_weather_query(query_id):
    resp = client.get(f"/api/weather-queries/{query_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == query_id
    print("PASS: test_read_weather_query")


def test_list_weather_queries():
    resp = client.get("/api/weather-queries")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1
    print("PASS: test_list_weather_queries")


def test_update_weather_query(query_id):
    with patch("app.routes.weather_routes.weather_service.geocode_location", new=AsyncMock(return_value=MOCK_LOCATION)), \
         patch("app.routes.weather_routes.weather_service.get_weather_for_range", new=AsyncMock(return_value=MOCK_WEATHER_DATA)):
        resp = client.put(f"/api/weather-queries/{query_id}", json={"location_input": "Bengaluru Updated"})
        assert resp.status_code == 200
        assert resp.json()["location_input"] == "Bengaluru Updated"
    print("PASS: test_update_weather_query")


def test_invalid_date_range_rejected():
    resp = client.post("/api/weather-queries", json={
        "location_input": "Bengaluru",
        "start_date": "2026-07-10T00:00:00",
        "end_date": "2026-07-05T00:00:00",  # end before start
    })
    assert resp.status_code == 422, resp.text  # pydantic validation catches this
    print("PASS: test_invalid_date_range_rejected")


def test_export_json(query_id):
    resp = client.get(f"/api/weather-queries/{query_id}/export", params={"format": "json"})
    assert resp.status_code == 200
    print("PASS: test_export_json")


def test_export_csv(query_id):
    resp = client.get(f"/api/weather-queries/{query_id}/export", params={"format": "csv"})
    assert resp.status_code == 200
    assert "date" in resp.text
    print("PASS: test_export_csv")


def test_export_pdf(query_id):
    resp = client.get(f"/api/weather-queries/{query_id}/export", params={"format": "pdf"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    print("PASS: test_export_pdf")


def test_create_event_and_assess_risk(query_id):
    resp = client.post("/api/events", json={
        "weather_query_id": query_id,
        "name": "Community Sports Day",
        "event_type": "sports",
        "start_time": "2026-07-06T09:00:00",
        "end_time": "2026-07-06T17:00:00",
    })
    assert resp.status_code == 201, resp.text
    event_id = resp.json()["id"]
    print(f"PASS: test_create_event -> id={event_id}")

    resp = client.post(f"/api/events/{event_id}/assess-risk")
    assert resp.status_code == 200, resp.text
    risk = resp.json()
    assert risk["overall_risk"] in ("Low", "Medium", "High")
    # July 6 mock data has temp_max=41 -> should be High heat risk
    assert risk["heat_risk"] == "High"
    print(f"PASS: test_assess_risk -> overall={risk['overall_risk']}, heat={risk['heat_risk']}")
    return event_id


def test_delete_weather_query(query_id):
    resp = client.delete(f"/api/weather-queries/{query_id}")
    assert resp.status_code == 204
    resp = client.get(f"/api/weather-queries/{query_id}")
    assert resp.status_code == 404
    print("PASS: test_delete_weather_query")


if __name__ == "__main__":
    qid = test_create_weather_query()
    test_read_weather_query(qid)
    test_list_weather_queries()
    test_update_weather_query(qid)
    test_invalid_date_range_rejected()
    test_export_json(qid)
    test_export_csv(qid)
    test_export_pdf(qid)
    test_create_event_and_assess_risk(qid)
    test_delete_weather_query(qid)
    print("\nAll integration tests passed.")

    # cleanup test db file
    if os.path.exists("test_weather_risk.db"):
        os.remove("test_weather_risk.db")
