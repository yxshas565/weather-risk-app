const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail;
    try {
      detail = (await res.json()).detail;
    } catch {
      detail = res.statusText;
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res.text();
}

export const api = {
  createWeatherQuery: (payload) =>
    request("/api/weather-queries", { method: "POST", body: JSON.stringify(payload) }),
  listWeatherQueries: () => request("/api/weather-queries"),
  getWeatherQuery: (id) => request(`/api/weather-queries/${id}`),
  updateWeatherQuery: (id, payload) =>
    request(`/api/weather-queries/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteWeatherQuery: (id) => request(`/api/weather-queries/${id}`, { method: "DELETE" }),
  exportUrl: (id, format) => `${API_BASE}/api/weather-queries/${id}/export?format=${format}`,

  createEvent: (payload) =>
    request("/api/events", { method: "POST", body: JSON.stringify(payload) }),
  assessRisk: (eventId) =>
    request(`/api/events/${eventId}/assess-risk`, { method: "POST" }),

  askAgent: (question, locationInput, startDate, endDate) =>
    request("/api/agent/ask", {
      method: "POST",
      body: JSON.stringify({
        question,
        location_input: locationInput || null,
        start_date: startDate || null,
        end_date: endDate || null,
      }),
    }),

  locationContext: (lat, lon) =>
    request(`/api/location-context?lat=${lat}&lon=${lon}`),
};

export default api;
