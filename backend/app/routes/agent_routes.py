from fastapi import APIRouter, HTTPException
from app.models.schemas import AgentQuery
from app.agent.weather_agent import run_agent

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/ask")
async def ask_agent(payload: AgentQuery):
    if not payload.question.strip():
        raise HTTPException(400, "question cannot be empty")
    result = await run_agent(
        payload.question,
        payload.location_input,
        payload.start_date,
        payload.end_date,
    )
    return result
