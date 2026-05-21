"""FastAPI routes for attack path operations."""

import threading
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import (
    get_graph_builder,
    get_mitre_mapper,
    get_path_finder,
    get_scorer,
    get_simulator,
    get_vulnerability_scorer,
)
from app.models.attack_path import (
    AttackPath,
    PathComputeRequest,
    PathComputeResponse,
    SimulationConfig,
    SimulationResult,
)
from app.models.graph import AttackEdge, AttackGraph, AttackNode
from app.services.graph_builder import AttackGraphBuilder
from app.services.mitre_mapping import MITREMapper
from app.services.path_finder import AttackPathFinder
from app.services.scoring import PathScorer
from app.services.simulation import MonteCarloSimulator
from app.services.vulnerability import VulnerabilityScorer

router = APIRouter()

# In-memory store for computed paths (bounded to MAX_STORED_PATHS)
MAX_STORED_PATHS = 1000
_computed_paths: list[AttackPath] = []
_paths_lock = threading.Lock()


def _get_demo_graph() -> AttackGraph:
    """Build a demonstration attack graph for path computation."""
    nodes = {
        "ext-attacker": AttackNode(
            id="ext-attacker", label="External Attacker", node_type="attacker",
            criticality=0.0, vulnerabilities=[], exploit_probability=1.0,
        ),
        "web-server": AttackNode(
            id="web-server", label="Web Server", node_type="server",
            criticality=0.7, vulnerabilities=["CVE-2023-44487"], exploit_probability=0.6,
        ),
        "app-server": AttackNode(
            id="app-server", label="Application Server", node_type="application",
            criticality=0.7, vulnerabilities=["CVE-2023-22515"], exploit_probability=0.7,
        ),
        "db-primary": AttackNode(
            id="db-primary", label="Primary Database", node_type="database",
            criticality=0.9, vulnerabilities=[], exploit_probability=0.3,
        ),
        "identity-svc": AttackNode(
            id="identity-svc", label="Identity Service", node_type="identity",
            criticality=0.8, vulnerabilities=[], exploit_probability=0.4,
        ),
        "firewall": AttackNode(
            id="firewall", label="Core Firewall", node_type="firewall",
            criticality=0.85, vulnerabilities=["CVE-2024-0012"], exploit_probability=0.5,
        ),
        "workstation": AttackNode(
            id="workstation", label="Admin Workstation", node_type="workstation",
            criticality=0.3, vulnerabilities=["CVE-2023-36884"], exploit_probability=0.5,
        ),
        "cloud-vm": AttackNode(
            id="cloud-vm", label="Cloud Analytics VM", node_type="cloud_vm",
            criticality=0.65, vulnerabilities=[], exploit_probability=0.3,
        ),
    }

    edges = [
        AttackEdge(source="ext-attacker", target="web-server", technique="T1190", probability=0.6),
        AttackEdge(source="ext-attacker", target="firewall", technique="T1190", probability=0.3),
        AttackEdge(source="web-server", target="app-server", technique="T1021", probability=0.7),
        AttackEdge(source="web-server", target="identity-svc", technique="T1078", probability=0.4),
        AttackEdge(source="app-server", target="db-primary", technique="T1210", probability=0.6),
        AttackEdge(source="app-server", target="cloud-vm", technique="T1021", probability=0.5),
        AttackEdge(source="identity-svc", target="workstation", technique="T1078", probability=0.5),
        AttackEdge(source="identity-svc", target="db-primary", technique="T1078", probability=0.3),
        AttackEdge(source="workstation", target="app-server", technique="T1570", probability=0.4),
        AttackEdge(source="firewall", target="web-server", technique="T1562", probability=0.5),
        AttackEdge(source="cloud-vm", target="db-primary", technique="T1210", probability=0.4),
    ]

    return AttackGraph(nodes=nodes, edges=edges)


@router.post("/compute", response_model=PathComputeResponse)
async def compute_attack_paths(
    request: PathComputeRequest,
    path_finder: AttackPathFinder = Depends(get_path_finder),
    scorer: PathScorer = Depends(get_scorer),
) -> PathComputeResponse:
    """Compute attack paths between entry points and targets."""
    global _computed_paths

    start_time = time.time()

    graph = _get_demo_graph()

    paths = path_finder.find_paths(
        graph=graph,
        entry_points=request.entry_points,
        targets=request.targets,
        max_depth=request.max_depth,
        include_techniques=request.include_techniques,
    )

    # Score and prioritize
    scored_paths = [scorer.score_path(p, graph) for p in paths]
    scored_paths = scorer.prioritize_paths(scored_paths)

    # Store for later retrieval (bounded, thread-safe)
    with _paths_lock:
        _computed_paths.extend(scored_paths)
        # Keep only the most recent paths if capacity is exceeded
        if len(_computed_paths) > MAX_STORED_PATHS:
            _computed_paths[:] = _computed_paths[-MAX_STORED_PATHS:]

    computation_time = (time.time() - start_time) * 1000

    return PathComputeResponse(
        paths=scored_paths,
        computation_time_ms=computation_time,
        total_paths_found=len(scored_paths),
    )


@router.get("", response_model=list[AttackPath])
async def list_attack_paths(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AttackPath]:
    """List all computed attack paths with pagination."""
    with _paths_lock:
        return _computed_paths[offset : offset + limit]


@router.get("/stats")
async def get_attack_path_stats() -> dict:
    """Get statistics about computed attack paths."""
    with _paths_lock:
        if not _computed_paths:
            return {
                "total_paths": 0,
                "average_risk_score": 0.0,
                "high_risk_count": 0,
                "average_steps": 0.0,
            }

        risk_scores = [p.total_risk_score for p in _computed_paths]
        steps_counts = [len(p.steps) for p in _computed_paths]

        return {
            "total_paths": len(_computed_paths),
            "average_risk_score": sum(risk_scores) / len(risk_scores),
            "high_risk_count": sum(1 for s in risk_scores if s > 0.7),
            "average_steps": sum(steps_counts) / len(steps_counts),
            "max_risk_score": max(risk_scores),
            "min_risk_score": min(risk_scores),
        }


@router.get("/techniques")
async def list_techniques(
    mitre_mapper: MITREMapper = Depends(get_mitre_mapper),
) -> list[dict]:
    """List all MITRE ATT&CK techniques."""
    techniques = mitre_mapper.get_all_techniques()
    return [
        {
            "id": t.id,
            "name": t.name,
            "tactic": t.tactic,
            "description": t.description,
            "applicable_asset_types": t.applicable_asset_types,
            "base_probability": t.base_probability,
        }
        for t in techniques.values()
    ]


@router.get("/techniques/{technique_id}")
async def get_technique(
    technique_id: str,
    mitre_mapper: MITREMapper = Depends(get_mitre_mapper),
) -> dict:
    """Get details for a specific MITRE technique."""
    technique = mitre_mapper.get_technique(technique_id)
    if technique is None:
        raise HTTPException(status_code=404, detail=f"Technique {technique_id} not found")
    return {
        "id": technique.id,
        "name": technique.name,
        "tactic": technique.tactic,
        "description": technique.description,
        "applicable_asset_types": technique.applicable_asset_types,
        "base_probability": technique.base_probability,
    }


@router.get("/vulnerabilities")
async def list_vulnerabilities(
    vuln_scorer: VulnerabilityScorer = Depends(get_vulnerability_scorer),
) -> list[dict]:
    """List sample vulnerabilities with computed probabilities."""
    cves = vuln_scorer.get_sample_cves()
    results = []
    for vuln in cves:
        base_prob = vuln_scorer.cvss_to_probability(vuln.cvss.base_score)
        adjusted_prob = vuln_scorer.adjust_for_exploit_availability(base_prob, vuln.exploit_available)
        adjusted_prob = vuln_scorer.adjust_for_patch_status(adjusted_prob, vuln.patch_available)
        results.append({
            "cve_id": vuln.cve_id,
            "description": vuln.description,
            "cvss_base_score": vuln.cvss.base_score,
            "exploit_available": vuln.exploit_available,
            "patch_available": vuln.patch_available,
            "base_probability": round(base_prob, 4),
            "adjusted_probability": round(adjusted_prob, 4),
        })
    return results


@router.post("/simulate", response_model=SimulationResult)
async def simulate_attack_path(
    config: SimulationConfig,
    simulator: MonteCarloSimulator = Depends(get_simulator),
) -> SimulationResult:
    """Run Monte Carlo simulation on a computed attack path."""
    # Find the path by ID
    target_path: Optional[AttackPath] = None
    with _paths_lock:
        for path in _computed_paths:
            if path.id == config.path_id:
                target_path = path
                break

    if target_path is None:
        raise HTTPException(status_code=404, detail=f"Path {config.path_id} not found")

    result = simulator.simulate(
        path=target_path,
        iterations=config.iterations,
        confidence_level=config.confidence_level,
    )

    return result


@router.get("/{path_id}", response_model=AttackPath)
async def get_attack_path(path_id: str) -> AttackPath:
    """Get a specific computed attack path by ID."""
    with _paths_lock:
        for path in _computed_paths:
            if path.id == path_id:
                return path
    raise HTTPException(status_code=404, detail=f"Path {path_id} not found")
