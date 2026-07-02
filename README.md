# 🌦️ Weather Risk Assistant

**PM Accelerator — AI Engineer Technical Assessment**
**Full Stack submission — Tech Assessment #1 (Frontend) + Tech Assessment #2 (Backend)**

Submitted by **Yashas Sadananda**
GitHub: [github.com/yxshas565](https://github.com/yxshas565)

---

## About PM Accelerator

> The Product Manager Accelerator Program is designed to support PM professionals through every stage of their careers. From students interested in becoming product managers to Directors looking to become Chief Product Officers, our program has helped over hundreds of students fulfill their career aspirations. Our Product Manager Accelerator community are ambitious and committed. Together, they have one thing in common: the desire to succeed.

---

## What this is

The assessment asks for a weather app. This *is* a weather app — every requirement below is implemented, tested, and working. But a plain "type a city, see the temperature" tool doesn't show much about how someone thinks.

So this app answers a more useful question than "what's the weather": **what should I actually *do* about it?**

Search a location, plan an event on any forecast day, and a **LangGraph agent** reasons over the live forecast — heat, rain, wind — to answer real questions in plain language: *"Should I plan an outdoor event this weekend?"* / *"Is it safe for construction work tomorrow?"* / *"I meant the event I planned on the 11th — is that still fine?"* The agent knows about saved events and resolves relative dates ("that day", "tomorrow") against them, giving a direct answer instead of a wall of numbers.

Nothing about this framing skips a requirement — it's built on top of a complete, spec-compliant CRUD weather app, not instead of one.

---

## ✅ Tech Assessment #1 — Frontend, mapped to spec

| Requirement | Status | Where |
|---|---|---|
| Enter location: ZIP/postal code, GPS coordinates, landmark, town, city | ✅ | `WeatherSearch.jsx` → backend geocoding (Open-Meteo + Nominatim fallback) |
| Show current weather clearly, with useful details | ✅ | `CurrentWeather.jsx` — temp, humidity, wind, precipitation, condition icon |
| See weather at current location | ✅ | "Use my location" button, browser Geolocation API |
| Icons/images for visual weather info | ✅ | Weather-code-mapped icon set |
| **5-day forecast**, clear/organized layout | ✅ | `Forecast.jsx` — responsive grid |
| **Error handling** — bad location, failed API calls | ✅ | Inline error banners, no silent failures; distinct messages per failure type |
| JS framework only, no Python/Java frontend | ✅ | React + Vite |
| Web-first responsive design | ✅ | CSS Grid + `auto-fit`/`minmax`, flex-wrap layouts, tested at desktop/tablet/mobile widths |
| Real API data, not static | ✅ | Open-Meteo live forecast API |

**Responsive technique used:** CSS Grid with `repeat(auto-fit, minmax())` for the forecast grid and stat cards, so column count reflows with viewport width without needing per-breakpoint media queries, plus a small set of targeted `@media (max-width: 480px)` rules for stacking the search row and header on narrow screens.

---

## ✅ Tech Assessment #2 — Backend, mapped to spec

| Requirement | Status | Where |
|---|---|---|
| **CREATE** — location + date range → temperature data, stored in DB | ✅ | `POST /api/weather-queries` |
| ↳ Validate date ranges | ✅ | Pydantic validator: `end_date` must be ≥ `start_date` |
| ↳ Validate location exists / fuzzy match | ✅ | Two-stage geocoding: Open-Meteo (city/town names) → Nominatim fallback (postal codes, landmarks, addresses) |
| **READ** — retrieve any stored weather query | ✅ | `GET /api/weather-queries`, `GET /api/weather-queries/{id}` — no row-level security, per spec note |
| **UPDATE** — modify stored weather info | ✅ | `PUT /api/weather-queries/{id}` |
| **DELETE** — remove records | ✅ | `DELETE /api/weather-queries/{id}` |
| SQL or NoSQL database | ✅ | SQLAlchemy + SQLite (swappable via `DATABASE_URL`) |
| **Data export**: JSON, XML, CSV, PDF, Markdown | ✅ | `GET /api/weather-queries/{id}/export?format=...` — all 5 formats |
| **Extra API integration** (stand-apart) | ✅ | OpenStreetMap/Nominatim location context, beyond the geocoding needed to resolve the query itself |
| RESTful API design | ✅ | FastAPI, resource-based routes, standard HTTP verbs + status codes |
| Requirements file | ✅ | `backend/requirements.txt` |

---

## 🧠 Beyond the spec: the Risk Assistant

This is the differentiator layer, built *after* every requirement above was working:

- **Rule-based risk scoring engine** — every forecast day is scored Low/Medium/High across heat, rain, and wind, with a plain-language explanation and a prep checklist per event type.
- **LangGraph agent** (`geocode → fetch_forecast → risk_score → reasoning`) — takes a natural-language question, resolves the location and the relevant date (explicit, relative, *or* by matching against saved events), fetches live forecast data, scores the risk, and has an LLM (OpenAI `gpt-4o-mini`) turn that into a short, direct answer.
- **Event-aware date resolution** — ask "is it safe on *that day*?" and the agent checks saved events for the one meant, instead of defaulting to today's forecast window.

---

## Architecture

```
frontend/                      React + Vite SPA
  src/
    components/                 WeatherSearch, CurrentWeather, Forecast, RiskAssistant, SavedQueries
    api.js                      fetch wrapper around the backend API
    App.jsx / App.css           layout, theming (dark/light toggle)

backend/
  app/
    database.py                 SQLAlchemy engine/session
    models/                     WeatherQuery, Event, RiskReport (SQLAlchemy + Pydantic schemas)
    routes/                     weather_routes, event_routes, agent_routes, location_routes
    services/
      weather_service.py         Open-Meteo client + two-stage geocoding
      risk_service.py            heat/rain/wind scoring engine
      export_service.py          JSON/CSV/XML/Markdown/PDF export
      location_context_service.py  OpenStreetMap integration
    agent/
      weather_agent.py           LangGraph agent definition
  main.py                       FastAPI entrypoint (PM Accelerator info lives here too)
  requirements.txt
```

---

## Running it locally

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
OPENAI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./weather.db   # optional — this is the default
```

```bash
uvicorn app.main:app --reload
```
Interactive API docs: `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App:
```bash 
weather-risk-ii7vqfjts-yxshas565s-projects.vercel.app
```

---

## Testing

```bash
cd backend
pytest
```
Covers the risk scoring engine, the weather/geocoding service, and end-to-end API integration.

---

## Notable bugs caught along the way

Real debugging, not a clean-room build — a few worth mentioning:

- **Risk threshold bug:** 7.6mm precipitation at 78% probability was originally scored "Low" risk. Caught by testing against live Bengaluru forecast data rather than synthetic test cases; fixed by tightening precipitation thresholds in `risk_service`.
- **LangGraph node/state collision:** a graph node named `"forecast"` collided with the state key also named `"forecast"`, causing silent overwrites. Renamed the node to `"fetch_forecast"`.
- **Geocoding coverage gap:** the initial single-provider geocoder only reliably resolved city/town names, not postal codes or landmarks. Added a Nominatim fallback for the cases Open-Meteo's gazetteer misses.
- **Agent/event disconnect:** the chat agent originally had no awareness of events actually planned, so "is it safe on *that day*?" would default to today's forecast instead of the planned event's date. Fixed by passing saved events into the agent's date-resolution step.
- **Model swap:** the agent originally targeted Anthropic's API; switched to OpenAI's `gpt-4o-mini` to keep the project runnable without requiring Anthropic credits from evaluators.

---

## Known limitation

Geocoding uses free providers (Open-Meteo + Nominatim). It reliably resolves cities, towns, landmarks, postal codes, and coordinates — hyper-specific street addresses with house numbers may occasionally fail to resolve. This is a constraint of free-tier geocoding services, not an app bug; a production deployment would swap in a paid geocoder (Google Maps, Mapbox) for full address-level precision.

## What's intentionally not included

Row-level security / per-user data segregation — explicitly out of scope per the assessment spec ("Row level security is not necessary to segment the data by users"). All saved queries are visible to any user of the app.

---

## In one line

Everything the assessment asked for was built first, fully — the Risk Assistant is what that data becomes useful *for* once it exists.
