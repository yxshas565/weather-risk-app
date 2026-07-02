# Weather Risk Assistant

Submitted by **Yashas Sadananda** for the PM Accelerator AI Engineer Technical Assessment (Full Stack — Tech Assessment #1 + #2).

A weather app that goes beyond "enter city, see weather." It reframes forecast data into **decision support** for the people who actually have to plan around it — event organizers, outdoor workers, sports coordinators — by scoring risk (heat / rain / wind), explaining *why*, and giving an LLM agent that can reason over the forecast to answer questions like *"which day this week is safest for an outdoor event?"*

Every literal requirement in the assessment is still fully implemented underneath this framing — nothing was skipped, the risk-assistant layer sits on top of a complete, spec-compliant weather app.

---

## About PM Accelerator

The Product Manager Accelerator Program is designed to support PM professionals through every stage of their careers. From students interested in becoming product managers to Directors looking to become Chief Product Officers, our program has helped over hundreds of students fulfill their career aspirations. Our Product Manager Accelerator community are ambitious and committed. Together, they have one thing in common: the desire to succeed.

---

## What's built

### Frontend (Tech Assessment #1)
- Location input — city, ZIP/postal code, landmark, or `lat,lon`, plus a "use my location" geolocation button
- Current weather with temperature, humidity, wind, precipitation, and condition icon
- 5-day forecast grid, responsive across desktop/tablet/mobile
- Inline event creation from any forecast day → feeds the risk engine
- Chat-style **Weather Risk Assistant** panel that calls the LangGraph agent
- Saved queries table with per-row export links and delete
- Dark/light theme toggle
- Graceful error handling (invalid location, failed API calls) surfaced as inline banners, not silent failures

**Stack:** React + Vite, plain CSS (no UI framework), CSS variables for theming, `fetch` for API calls.

### Backend (Tech Assessment #2)
- **CRUD** on weather queries: create (location + date range → live Open-Meteo data, with location and date-range validation), read (list/detail), update, delete
- **Event model** with a rule-based risk scoring engine (heat / rain / wind thresholds → Low / Medium / High) that returns explanations and a prep checklist per event
- **Data export** to JSON, CSV, XML, Markdown, and PDF
- **Extra API integration:** OpenStreetMap for location context (beyond the geocoding needed to resolve the query itself)
- **LangGraph agent:** geocode → fetch forecast → score risk → LLM reasoning, exposed as a chat endpoint the frontend calls directly. Uses OpenAI (`gpt-4o-mini`) for the reasoning step.
- SQLAlchemy models on a relational database (SQLite by default, swappable via `DATABASE_URL`)

**Stack:** FastAPI, SQLAlchemy, LangGraph, OpenAI SDK, ReportLab (PDF export), httpx.

---

## Architecture

```
frontend/               React + Vite SPA
  src/
    components/          WeatherSearch, CurrentWeather, Forecast, RiskAssistant, SavedQueries
    api.js                thin fetch wrapper around the backend API
    App.jsx / App.css

backend/
  app/
    database.py           SQLAlchemy engine/session setup
    models/                WeatherQuery, Event
    routes/                weather_routes, event_routes, agent_routes, location_routes
    services/              risk_service (scoring engine), weather_service (Open-Meteo client), export_service
    agent/                 LangGraph graph definition (geocode -> fetch_forecast -> risk-score -> reasoning)
  main.py                  FastAPI app entrypoint
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

Create a `.env` file in `backend/`:
```
OPENAI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./weather.db   # optional, this is the default
```

```bash
uvicorn main:app --reload
```
API docs available at `http://localhost:8000/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App available at `http://localhost:5173`.

---

## Testing

Backend test suites (pytest) cover the risk scoring engine, the weather service, and API integration end-to-end:
```bash
cd backend
pytest
```

---

## Notable engineering decisions / bugs caught along the way

- **Risk threshold bug:** the original scoring logic classified 7.6mm precipitation at 78% probability as "Low" risk — a real bug caught by testing against live Bengaluru forecast data, not synthetic test cases. Fixed by tightening the precipitation thresholds in `risk_service`.
- **LangGraph node/state collision:** a graph node named `"forecast"` collided with the state key also named `"forecast"`, causing silent state overwrites. Renamed the node to `"fetch_forecast"` to resolve it.
- **Model swap:** the agent originally targeted Anthropic's API; switched to OpenAI's `gpt-4o-mini` for the reasoning step to keep the project runnable without requiring Anthropic credits from evaluators.

---

## What's not included (by design)

Row-level security / per-user data segregation was explicitly out of scope per the assessment spec — all saved queries are visible to any user of the app, matching the "Row level security is not necessary" note in Tech Assessment #2.

---

## Differentiator, in one line

Everything the assessment asked for was built first; the Weather Risk Assistant is what that data becomes useful *for* once it exists.