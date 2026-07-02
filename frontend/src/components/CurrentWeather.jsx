const WEATHER_ICONS = {
  0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
  45: "🌫️", 48: "🌫️",
  51: "🌦️", 53: "🌦️", 55: "🌧️",
  61: "🌧️", 63: "🌧️", 65: "⛈️",
  71: "🌨️", 73: "🌨️", 75: "❄️",
  80: "🌦️", 81: "🌧️", 82: "⛈️",
  95: "⛈️", 96: "⛈️", 99: "⛈️",
};

function iconFor(code) {
  return WEATHER_ICONS[code] ?? "🌡️";
}

export default function CurrentWeather({ query }) {
  let weather;
  try {
    weather = JSON.parse(query.weather_data || "{}");
  } catch {
    weather = {};
  }
  const current = weather.current;

  if (!current) {
    return (
      <div className="card current-weather">
        <p>No current weather data available for this query.</p>
      </div>
    );
  }

  return (
    <div className="card current-weather">
      <div className="current-header">
        <div>
          <h2>{query.resolved_name}</h2>
          <p className="coords">
            {query.latitude.toFixed(3)}, {query.longitude.toFixed(3)}
          </p>
        </div>
        <div className="current-icon">{iconFor(current.weathercode)}</div>
      </div>
      <div className="current-stats">
        <div className="stat">
          <span className="stat-value">{Math.round(current.temperature_2m)}°C</span>
          <span className="stat-label">Temperature</span>
        </div>
        <div className="stat">
          <span className="stat-value">{current.relative_humidity_2m}%</span>
          <span className="stat-label">Humidity</span>
        </div>
        <div className="stat">
          <span className="stat-value">{current.windspeed_10m} km/h</span>
          <span className="stat-label">Wind</span>
        </div>
        <div className="stat">
          <span className="stat-value">{current.precipitation} mm</span>
          <span className="stat-label">Precipitation</span>
        </div>
      </div>
    </div>
  );
}

export { iconFor };
