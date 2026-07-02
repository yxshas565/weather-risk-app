import { useState } from "react";
import api from "../api";

const todayISO = () => new Date().toISOString().slice(0, 10);
const inDaysISO = (days) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
};

export default function WeatherSearch({ onQueryCreated, onError }) {
  const [location, setLocation] = useState("");
  const [startDate, setStartDate] = useState(todayISO());
  const [endDate, setEndDate] = useState(inDaysISO(4)); // 5-day window inclusive
  const [loading, setLoading] = useState(false);
  const [geoLoading, setGeoLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!location.trim()) {
      onError("Please enter a location.");
      return;
    }
    setLoading(true);
    onError(null);
    try {
      const query = await api.createWeatherQuery({
        location_input: location.trim(),
        start_date: `${startDate}T00:00:00`,
        end_date: `${endDate}T00:00:00`,
      });
      onQueryCreated(query);
    } catch (err) {
      onError(err.message);
      onQueryCreated(null);
    } finally {
      setLoading(false);
    }
  };

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      onError("Geolocation is not supported by this browser.");
      return;
    }
    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation(`${pos.coords.latitude.toFixed(4)},${pos.coords.longitude.toFixed(4)}`);
        setGeoLoading(false);
      },
      (err) => {
        onError(`Could not get your location: ${err.message}`);
        setGeoLoading(false);
      }
    );
  };

  return (
    <form className="weather-search" onSubmit={submit}>
      <div className="search-row">
        <input
          type="text"
          placeholder="City, ZIP/postal code, landmark, or lat,lon"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <button type="button" onClick={useMyLocation} disabled={geoLoading} className="secondary-btn">
          {geoLoading ? "Locating..." : "📍 Use my location"}
        </button>
      </div>
      <div className="search-row">
        <label>
          From
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </label>
        <label>
          To
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </label>
        <button type="submit" disabled={loading} className="primary-btn">
          {loading ? "Fetching..." : "Get Weather"}
        </button>
      </div>
    </form>
  );
}
