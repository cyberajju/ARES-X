"""ARES-X Attack Path Engine - FastAPI Application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    print("ARES-X Attack Path Engine starting up...")
    yield
    # Shutdown
    print("ARES-X Attack Path Engine shutting down...")


app = FastAPI(
    title="ARES-X Attack Path Engine",
    description="Attack path computation, MITRE ATT&CK mapping, and Monte Carlo simulation engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1/attack-paths")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "attack-path-engine", "version": "0.1.0"}
