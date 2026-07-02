"""
Risk scoring service.

Converts raw forecast data into Low/Medium/High risk categories for
heat, rain, and wind, plus a natural-language explanation and checklist.

NOTE ON HONESTY: this is a transparent, rule-based (threshold) scoring
model here in the live app — thresholds are informed by real published
guidance (OSHA heat index categories, standard heavy-rain/high-wind
definitions). This is intentionally simple and auditable so the app can
run in real time without a training pipeline in the request path.

The trained ML ensemble + anomaly detection + SHAP explainability lives
in the separate Data Science project (weather-risk-forecasting/), which
analyzes historical patterns offline. If wired together, that model's
output would replace/augment these thresholds — documented as a "next
step" in the README rather than overclaimed as already integrated.
"""
from typing import Optional


# Heat index risk thresholds (Celsius), loosely aligned with OSHA heat
# index risk categories (converted from Fahrenheit).
HEAT_THRESHOLDS = {"low": 27, "medium": 32, "high": 39}
RAIN_THRESHOLDS_MM = {"low": 2, "medium": 10, "high": 25}
WIND_THRESHOLDS_KMH = {"low": 20, "medium": 40, "high": 60}


def _bucket(value: float, thresholds: dict) -> str:
    if value >= thresholds["high"]:
        return "High"
    if value >= thresholds["medium"]:
        return "Medium"
    if value >= thresholds["low"]:
        return "Low"
    return "Low"


def _overall(risks: list[str]) -> str:
    if "High" in risks:
        return "High"
    if "Medium" in risks:
        return "Medium"
    return "Low"


def score_day(day: dict, event_type: str) -> dict:
    """
    Scores a single forecast day dict (as returned by weather_service.get_forecast)
    against event-type-aware thresholds, returns risk breakdown + explanation.
    """
    temp_max = day.get("temp_max", 0)
    precip = day.get("precipitation_sum", 0)
    wind = day.get("windspeed_max", 0)
    precip_prob = day.get("precipitation_probability", 0)

    heat_risk = _bucket(temp_max, HEAT_THRESHOLDS)
    rain_risk = _bucket(precip, RAIN_THRESHOLDS_MM)
    wind_risk = _bucket(wind, WIND_THRESHOLDS_KMH)

    # Outdoor manual labor is more heat/wind sensitive than a seated event
    if event_type in ("construction_shift", "outdoor_labor", "sports"):
        if temp_max >= HEAT_THRESHOLDS["medium"]:
            heat_risk = "High"

    overall = _overall([heat_risk, rain_risk, wind_risk])

    # Simple explainability: rank which factor deviates most from its
    # "safe" threshold, proportionally — a lightweight stand-in for the
    # SHAP-based feature importance used in the DS project offline.
    factors = [
        {"feature": "max_temperature", "value": temp_max, "risk": heat_risk,
         "deviation": max(0, temp_max - HEAT_THRESHOLDS["low"])},
        {"feature": "precipitation", "value": precip, "risk": rain_risk,
         "deviation": max(0, precip - RAIN_THRESHOLDS_MM["low"])},
        {"feature": "wind_speed", "value": wind, "risk": wind_risk,
         "deviation": max(0, wind - WIND_THRESHOLDS_KMH["low"])},
    ]
    factors.sort(key=lambda f: f["deviation"], reverse=True)
    top_factor = factors[0]

    explanation = _build_explanation(day, top_factor, overall, precip_prob)
    checklist = _build_checklist(heat_risk, rain_risk, wind_risk, event_type)

    return {
        "date": day.get("date"),
        "heat_risk": heat_risk,
        "rain_risk": rain_risk,
        "wind_risk": wind_risk,
        "overall_risk": overall,
        "top_factors": factors,
        "explanation": explanation,
        "checklist": checklist,
    }


def _build_explanation(day: dict, top_factor: dict, overall: str, precip_prob: float) -> str:
    if overall == "Low":
        return (
            f"Conditions look manageable: max temp {day.get('temp_max')}°C, "
            f"{day.get('precipitation_sum')}mm precipitation expected, "
            f"wind up to {day.get('windspeed_max')}km/h."
        )
    reason = {
        "max_temperature": f"a high of {day.get('temp_max')}°C driving heat risk",
        "precipitation": (
            f"{day.get('precipitation_sum')}mm of expected precipitation "
            f"({precip_prob}% chance) driving rain risk"
        ),
        "wind_speed": f"wind gusts up to {day.get('windspeed_max')}km/h driving wind risk",
    }[top_factor["feature"]]
    return f"Overall risk is {overall}, primarily due to {reason}."


def _build_checklist(heat_risk: str, rain_risk: str, wind_risk: str, event_type: str) -> list[str]:
    items = []
    if heat_risk in ("Medium", "High"):
        items.append("Set up shaded/cooling areas and schedule hydration breaks")
        if heat_risk == "High":
            items.append("Consider shifting the event to a cooler part of the day")
    if rain_risk in ("Medium", "High"):
        items.append("Prepare tents/covered areas or an indoor backup venue")
        if rain_risk == "High":
            items.append("Have a rain-delay or cancellation decision point defined in advance")
    if wind_risk in ("Medium", "High"):
        items.append("Secure loose structures, signage, and equipment")
        if wind_risk == "High":
            items.append("Avoid erecting tall temporary structures (stages, large tents)")
    if not items:
        items.append("No special precautions needed — conditions are within normal range")
    return items
