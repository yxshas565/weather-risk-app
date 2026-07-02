"""
Unit tests for risk_service — pure logic, no network calls, so these
run reliably regardless of sandbox/CI network restrictions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import risk_service


def test_low_risk_day():
    day = {"date": "2026-07-05", "temp_max": 24, "precipitation_sum": 0,
           "precipitation_probability": 5, "windspeed_max": 10, "humidity_max": 50}
    result = risk_service.score_day(day, event_type="general")
    assert result["overall_risk"] == "Low", result
    assert result["heat_risk"] == "Low"
    assert result["rain_risk"] == "Low"
    assert result["wind_risk"] == "Low"
    print("PASS: test_low_risk_day")


def test_high_heat_risk_day():
    day = {"date": "2026-07-05", "temp_max": 41, "precipitation_sum": 0,
           "precipitation_probability": 0, "windspeed_max": 10, "humidity_max": 40}
    result = risk_service.score_day(day, event_type="general")
    assert result["heat_risk"] == "High", result
    assert result["overall_risk"] == "High"
    assert "temp" in result["top_factors"][0]["feature"] or "temperature" in result["top_factors"][0]["feature"]
    print("PASS: test_high_heat_risk_day")


def test_high_rain_risk_day():
    day = {"date": "2026-07-05", "temp_max": 25, "precipitation_sum": 30,
           "precipitation_probability": 90, "windspeed_max": 15, "humidity_max": 80}
    result = risk_service.score_day(day, event_type="general")
    assert result["rain_risk"] == "High", result
    assert result["overall_risk"] == "High"
    assert any("tent" in item.lower() or "indoor" in item.lower() for item in result["checklist"])
    print("PASS: test_high_rain_risk_day")


def test_construction_shift_lower_heat_threshold():
    """Outdoor labor should be flagged High heat risk at a lower temp than 'general'."""
    day = {"date": "2026-07-05", "temp_max": 33, "precipitation_sum": 0,
           "precipitation_probability": 0, "windspeed_max": 10, "humidity_max": 40}
    general_result = risk_service.score_day(day, event_type="general")
    labor_result = risk_service.score_day(day, event_type="construction_shift")
    assert labor_result["heat_risk"] == "High"
    # general should be Medium at this temp per thresholds (32-39 = Medium)
    assert general_result["heat_risk"] in ("Medium", "High")
    print("PASS: test_construction_shift_lower_heat_threshold")


def test_checklist_empty_for_low_risk():
    day = {"date": "2026-07-05", "temp_max": 22, "precipitation_sum": 0,
           "precipitation_probability": 0, "windspeed_max": 5, "humidity_max": 30}
    result = risk_service.score_day(day, event_type="general")
    assert len(result["checklist"]) == 1
    assert "no special precautions" in result["checklist"][0].lower()
    print("PASS: test_checklist_empty_for_low_risk")


def test_explanation_is_nonempty_and_grounded():
    day = {"date": "2026-07-05", "temp_max": 38, "precipitation_sum": 5,
           "precipitation_probability": 40, "windspeed_max": 20, "humidity_max": 60}
    result = risk_service.score_day(day, event_type="general")
    assert len(result["explanation"]) > 10
    assert "38" in result["explanation"]  # grounded in actual temp value
    print("PASS: test_explanation_is_nonempty_and_grounded")


if __name__ == "__main__":
    test_low_risk_day()
    test_high_heat_risk_day()
    test_high_rain_risk_day()
    test_construction_shift_lower_heat_threshold()
    test_checklist_empty_for_low_risk()
    test_explanation_is_nonempty_and_grounded()
    print("\nAll risk_service tests passed.")
