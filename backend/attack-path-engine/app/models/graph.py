"""Graph representation models for attack paths."""

from pydantic import BaseModel, Field


class AttackNode(BaseModel):
    """A node in the attack graph representing an asset."""

    id: str
    label: str
    node_type: str
    criticality: float = Field(ge=0.0, le=1.0)
    vulnerabilities: list[str] = Field(default_factory=list)
    exploit_probability: float = Field(default=0.0, ge=0.0, le=1.0)


class AttackEdge(BaseModel):
    """An edge in the attack graph representing a possible lateral movement."""

    source: str
    target: str
    technique: str = ""
    probability: float = Field(ge=0.0, le=1.0)
    prerequisites: list[str] = Field(default_factory=list)


class AttackGraph(BaseModel):
    """The complete attack graph."""

    nodes: dict[str, AttackNode] = Field(default_factory=dict)
    edges: list[AttackEdge] = Field(default_factory=list)
