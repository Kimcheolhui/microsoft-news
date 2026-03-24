"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import reports, sources, stats, updates

app = FastAPI(
    title="Azure Ingest API",
    version="0.1.0",
    description="REST API for Azure ecosystem updates and analysis reports",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(updates.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
