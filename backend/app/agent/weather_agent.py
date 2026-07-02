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
from anthropic import Anthropic

from app.services import weather_service, risk_service

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class AgentState(TypedDict):
    question: str
    location_input: Optional[str]
    location: Optional[dict]
    forecast: Optional[list]
    risk_assessment: Optional[dict]
    answer: Optional[str]
    error: Optional[str]


async def geocode_node(state: AgentState) -> AgentState:
    loc_input = state.get("location_input")
    if not loc_input:
        # Try to extract a location mention from the question itself via LLM
        loc_input = await _extract_location(state["question"])
        if not loc_input:
            state["error"] = "Couldn't identify a location in your question. Please specify one."
            return state
    try:
        state["location"] = await weather_service.geocode_location(loc_input)
    except weather_service.WeatherServiceError as e:
        state["error"] = str(e)
    return state


async def forecast_node(state: AgentState) -> AgentState:
    if state.get("error") or not state.get("location"):
        return state
    try:
        loc = state["location"]
        state["forecast"] = await weather_service.get_forecast(loc["latitude"], loc["longitude"], days=7)
    except weather_service.WeatherServiceError as e:
        state["error"] = str(e)
    return state


def risk_node(state: AgentState) -> AgentState:
    if state.get("error") or not state.get("forecast"):
        return state
    # Score the nearest upcoming day as a default; the reasoning node
    # can reference the full week if the question implies a range.
    scored_days = [risk_service.score_day(day, event_type="general") for day in state["forecast"]]
    state["risk_assessment"] = {"days": scored_days}
    return state


async def reasoning_node(state: AgentState) -> AgentState:
    """Final node: LLM synthesizes tool outputs into a decision-oriented answer."""
    if state.get("error"):
        state["answer"] = f"I couldn't complete that request: {state['error']}"
        return state

    context = {
        "location": state["location"],
        "risk_by_day": state["risk_assessment"]["days"],
    }

    prompt = f"""You are a weather risk assistant. A user asked: "{state['question']}"

Here is real forecast + risk data for their location over the next 7 days:
{json.dumps(context, indent=2, default=str)}

Answer the user's question directly and specifically, using this data. Be decision-oriented:
give a clear recommendation, cite the specific numbers driving your reasoning, and flag
which day(s) if any carry elevated risk. Keep it concise (3-5 sentences), no fluff."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        state["answer"] = "".join(
            block.text for block in response.content if block.type == "text"
        )
    except Exception as e:
        state["answer"] = (
            "I gathered the weather data but couldn't generate a natural-language "
            f"summary (LLM error: {e}). Raw risk data: {json.dumps(context, default=str)}"
        )
    return state


async def _extract_location(question: str) -> Optional[str]:
    """Lightweight LLM call to pull a location mention out of free text."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
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
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        return None if text.upper() == "NONE" else text
    except Exception:
        return None


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("geocode", geocode_node)
    graph.add_node("forecast", forecast_node)
    graph.add_node("risk", risk_node)
    graph.add_node("reasoning", reasoning_node)

    graph.set_entry_point("geocode")
    graph.add_edge("geocode", "forecast")
    graph.add_edge("forecast", "risk")
    graph.add_edge("risk", "reasoning")
    graph.add_edge("reasoning", END)

    return graph.compile()


_compiled_graph = None


async def run_agent(question: str, location_input: Optional[str] = None) -> dict:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()

    initial_state: AgentState = {
        "question": question,
        "location_input": location_input,
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
