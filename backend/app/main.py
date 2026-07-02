"""
Weather Risk Assistant — main FastAPI application.

Built for the PM Accelerator AI Engineer + Data Science internship
technical assessment.

Submitted by: Yashas Sadananda

---
About PM Accelerator (from company LinkedIn):
The Product Manager Accelerator Program is designed to support PM
professionals through every stage of their careers. From students
interested in becoming product managers to Directors looking to
become Chief Product Officers, our program has helped over hundreds
of students fulfill their career aspirations. Our Product Manager
Accelerator community are ambitious and committed. Together, they
have one thing in common: the desire to succeed.
---
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import weather_routes, event_routes, agent_routes, location_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Weather Risk Assistant API",
    description=(
        "Weather app + decision-support risk assistant, built for the "
        "PM Accelerator AI Engineer technical assessment."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened in production deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weather_routes.router)
app.include_router(event_routes.router)
app.include_router(agent_routes.router)
app.include_router(location_routes.router)


@app.get("/")
def root():
    return {
        "service": "Weather Risk Assistant API",
        "author": "Yashas Sadananda",
        "docs": "/docs",
        "about_pm_accelerator": (
            "The Product Manager Accelerator Program is designed to support PM "
            "professionals through every stage of their careers."
        ),
    }


@app.get("/health")
def health():
    return {"status": "ok"}
