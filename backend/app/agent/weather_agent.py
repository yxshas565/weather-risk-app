"""
Weather Risk Agent — LangGraph orchestration.

Takes a natural-language question + location, and runs a tool-calling
loop: geocode -> forecast -> risk-score -> explain, then returns a
decision-oriented answer instead of raw numbers.

This is intentionally a small, readable graph (not over-engineered) —
depth here comes from what each node actually does (real risk scoring,
real explanations), not from graph complexity for its own sake.
"""
import json
import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from openai import OpenAI


from app.services import weather_service, risk_service

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AgentState(TypedDict):
    question: str
    location_input: Optional[str]
    start_date: Optional[object]
    end_date: Optional[object]
    question_date: Optional[str]
    events: Optional[list]
    location: Optional[dict]
    used_fallback_location: Optional[bool]
    forecast: Optional[list]
    risk_assessment: Optional[dict]
    answer: Optional[str]
    error: Optional[str]


async def geocode_node(state: AgentState) -> AgentState:
    # Prefer a location explicitly mentioned in the question; fall back to
    # the active query's location if the question doesn't name one.
    extracted = await _extract_location(state["question"])
    loc_input = extracted or state.get("location_input")
    if not loc_input:
        state["error"] = "Couldn't identify a location. Please specify one or select a saved query."
        return state
    state["used_fallback_location"] = extracted is None
    try:
        state["location"] = await weather_service.geocode_location(loc_input)
    except weather_service.WeatherServiceError as e:
        state["error"] = str(e)

    # Try to pull an explicit date/day reference out of the question
    # (e.g. "that day", "July 5th", "tomorrow") so questions about a
    # specific planned event resolve to the right date, not just "today".
    events = state.get("events") or []
    extracted_date = await _extract_date(state["question"], events)
    if extracted_date:
        state["question_date"] = extracted_date
    return state


async def forecast_node(state: AgentState) -> AgentState:
    if state.get("error") or not state.get("location"):
        return state
    try:
        loc = state["location"]
        start = state.get("start_date")
        end = state.get("end_date")
        q_date = state.get("question_date")

        if q_date:
            # A specific date was mentioned/implied in the question —
            # fetch a tight window around it so the agent answers about
            # that day specifically, not just "today onward".
            from datetime import datetime as _dt
            q_date_obj = _dt.strptime(q_date, "%Y-%m-%d").date()
            state["forecast"] = await weather_service.get_forecast(
                loc["latitude"], loc["longitude"], start_date=q_date_obj, end_date=q_date_obj
            )
        elif state.get("used_fallback_location") and start and end:
            state["forecast"] = await weather_service.get_forecast(
                loc["latitude"], loc["longitude"], start_date=start, end_date=end
            )
        else:
            state["forecast"] = await weather_service.get_forecast(loc["latitude"], loc["longitude"], days=7)
    except weather_service.WeatherServiceError as e:
        state["error"] = str(e)
    return state


def risk_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    if not state.get("forecast"):
        state["error"] = (
            "No forecast data is available for that date range. The free forecast API "
            "only covers up to 16 days ahead — try a closer date range."
        )
        return state
    scored_days = [risk_service.score_day(day, event_type="general") for day in state["forecast"]]
    state["risk_assessment"] = {"days": scored_days}
    return state


async def reasoning_node(state: AgentState) -> AgentState:
    """Final node: LLM synthesizes tool outputs into a decision-oriented answer."""
    if state.get("error") or not state.get("risk_assessment"):
        state["answer"] = f"I couldn't complete that request: {state.get('error') or 'No risk data available.'}"
        return state

    context = {
        "location": state["location"],
        "risk_by_day": state["risk_assessment"]["days"],
    }

    prompt = f"""You are a sharp, decisive weather advisor talking to a real person. They asked: "{state['question']}"

Real forecast + risk data for their location, next 7 days:
{json.dumps(context, indent=2, default=str)}

Write your answer like a knowledgeable friend, not a report. Rules:
- Open with a direct yes/no/go-ahead answer in the first sentence — no throat-clearing, no "Based on the data..."
- Use natural, conversational phrasing. Contractions are fine. Vary sentence length.
- Weave in only the 2-3 numbers that actually matter for the decision — skip the rest.
- If risk is genuinely low, say so plainly and move on — don't manufacture caveats.
- If risk is elevated on a specific day, name that day and say what to actually do about it (one concrete action, not a checklist).
- Max 3 sentences. Every sentence must earn its place.
- Never say "risk assessment," "overall risk," or repeat the word "risk" more than twice total."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        state["answer"] = response.choices[0].message.content
    except Exception as e:
        state["answer"] = (
            "I gathered the weather data but couldn't generate a natural-language "
            f"summary (LLM error: {e}). Raw risk data: {json.dumps(context, default=str)}"
        )
    return state


async def _extract_location(question: str) -> Optional[str]:
    """Lightweight LLM call to pull a location mention out of free text."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    f"Extract only the location name mentioned in this question, "
                    f"or respond with exactly 'NONE' if no location is mentioned. "
                    f"Question: \"{question}\""
                ),
            }],
        )
        text = response.choices[0].message.content.strip()
        return None if text.upper() == "NONE" else text
    except Exception:
        return None
    

async def _extract_date(question: str, events: Optional[list] = None) -> Optional[str]:
    """Pulls an explicit or relative date reference out of free text,
    resolved to YYYY-MM-DD. Knows about the user's saved events so
    'that day' / event names can resolve without the date being retyped."""
    from datetime import date
    today_str = date.today().isoformat()
    events = events or []
    events_str = "\n".join(
        f"- \"{e.get('name')}\" on {e.get('start_time', '')[:10]}" for e in events
    ) or "(none)"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": (
                    f"Today's date is {today_str}. The user has these saved events:\n"
                    f"{events_str}\n\n"
                    f"They asked: \"{question}\"\n"
                    f"If the question refers to a specific date — explicitly (e.g. "
                    f"'July 5th'), relatively (e.g. 'tomorrow'), or by referring to "
                    f"one of the saved events above (e.g. 'that day', 'the football "
                    f"turf event') — respond with just that date in YYYY-MM-DD format. "
                    f"If no date can be determined, respond with exactly 'NONE'."
                ),
            }],
        )
        text = response.choices[0].message.content.strip()
        return None if text.upper() == "NONE" else text
    except Exception:
        return None


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("geocode", geocode_node)
    graph.add_node("fetch_forecast", forecast_node)
    graph.add_node("risk", risk_node)
    graph.add_node("reasoning", reasoning_node)

    graph.set_entry_point("geocode")
    graph.add_edge("geocode", "fetch_forecast")
    graph.add_edge("fetch_forecast", "risk")
    graph.add_edge("risk", "reasoning")
    graph.add_edge("reasoning", END)

    return graph.compile()


_compiled_graph = None


async def run_agent(
    question: str,
    location_input: Optional[str] = None,
    start_date=None,
    end_date=None,
    events: Optional[list] = None,
) -> dict:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()

    initial_state: AgentState = {
        "question": question,
        "location_input": location_input,
        "start_date": start_date,
        "end_date": end_date,
        "events": events,
        "location": None,
        "forecast": None,
        "risk_assessment": None,
        "answer": None,
        "error": None,
    }

    final_state = await _compiled_graph.ainvoke(initial_state)
    return {
        "answer": final_state.get("answer"),
        "location": final_state.get("location"),
        "risk_assessment": final_state.get("risk_assessment"),
        "error": final_state.get("error"),
    }