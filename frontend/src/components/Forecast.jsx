import { useState } from "react";
import { iconFor } from "./CurrentWeather";
import api from "../api";

export default function Forecast({ query, onEventCreated }) {
  const [creatingFor, setCreatingFor] = useState(null); // date string
  const [eventName, setEventName] = useState("");
  const [eventType, setEventType] = useState("general");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  let weather;
  try {
    weather = JSON.parse(query.weather_data || "{}");
  } catch {
    weather = {};
  }
  const forecast = weather.forecast || [];

  if (forecast.length === 0) {
    return (
      <div className="card">
        <p>No forecast data available.</p>
      </div>
    );
  }

  const createEventForDay = async (day) => {
    if (!eventName.trim()) {
      setMsg("Enter an event name first.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      await api.createEvent({
        weather_query_id: query.id,
        name: eventName.trim(),
        event_type: eventType,
        start_time: `${day.date}T09:00:00`,
        end_time: `${day.date}T17:00:00`,
      });
      setMsg(`Event "${eventName}" created for ${day.date}. See it in the Risk Assistant panel below.`);
      setCreatingFor(null);
      setEventName("");
      onEventCreated?.();
    } catch (err) {
      setMsg(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h3>{forecast.length}-Day Forecast</h3>
      <div className="forecast-grid">
        {forecast.map((day) => (
          <div key={day.date} className="forecast-day">
            <div className="forecast-date">
              {new Date(day.date).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
            </div>
            <div className="forecast-icon">{iconFor(day.weathercode)}</div>
            <div className="forecast-temps">
              <span className="temp-max">{Math.round(day.temp_max)}°</span>
              <span className="temp-min">{Math.round(day.temp_min)}°</span>
            </div>
            <div className="forecast-detail">💧 {day.precipitation_probability}%</div>
            <div className="forecast-detail">💨 {Math.round(day.windspeed_max)} km/h</div>
            <button
              className="link-btn"
              onClick={() => setCreatingFor(creatingFor === day.date ? null : day.date)}
            >
              {creatingFor === day.date ? "Cancel" : "+ Plan event"}
            </button>
            {creatingFor === day.date && (
              <div className="event-create-inline">
                <input
                  type="text"
                  placeholder="Event name"
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                />
                <select value={eventType} onChange={(e) => setEventType(e.target.value)}>
                  <option value="general">General</option>
                  <option value="outdoor_event">Outdoor Event</option>
                  <option value="construction_shift">Construction Shift</option>
                  <option value="sports">Sports</option>
                </select>
                <button disabled={busy} onClick={() => createEventForDay(day)} className="primary-btn small">
                  {busy ? "Creating..." : "Assess Risk"}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
      {msg && <p className="inline-msg">{msg}</p>}
    </div>
  );
}
