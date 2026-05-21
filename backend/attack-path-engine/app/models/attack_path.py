"""Attack path Pydantic models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PathStep(BaseModel):
    """A single step in an attack path."""

    node_id: str
    node_name: str
    node_type: str
    technique_id: str = ""
    technique_name: str = ""
    probability: float = Field(ge=0.0, le=1.0)
    cumulative_risk: float = Field(ge=0.0, le=1.0)


class AttackPath(BaseModel):
    """A complete attack path from entry point to target."""

    id: str
    name: str
    steps: list[PathStep]
    total_risk_score: float = Field(ge=0.0, le=1.0)
    exploitability: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)
    entry_point: str
    target: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PathComputeRequest(BaseModel):
    """Request to compute attack paths."""

    entry_points: list[str]
    targets: list[str]
    max_depth: int = Field(default=10, ge=1, le=50)
    include_techniques: bool = True


class PathComputeResponse(BaseModel):
    """Response from attack path computation."""

    paths: list[AttackPath]
    computation_time_ms: float
    total_paths_found: int


class SimulationConfig(BaseModel):
    """Configuration for Monte Carlo simulation."""

    path_id: str
    iterations: int = Field(default=10000, ge=100, le=1000000)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)


class SimulationResult(BaseModel):
    """Result of a Monte Carlo simulation."""

    path_id: str
    mean_probability: float
    std_deviation: float
    confidence_interval: tuple[float, float]
    percentiles: dict[str, float]
    iterations_run: int
    converged: bool
