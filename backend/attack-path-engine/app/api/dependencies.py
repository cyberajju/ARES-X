"""FastAPI dependencies for service injection."""

from app.services.graph_builder import AttackGraphBuilder
from app.services.mitre_mapping import MITREMapper
from app.services.path_finder import AttackPathFinder
from app.services.scoring import PathScorer
from app.services.simulation import MonteCarloSimulator
from app.services.vulnerability import VulnerabilityScorer

# Singleton service instances
_graph_builder: AttackGraphBuilder | None = None
_path_finder: AttackPathFinder | None = None
_simulator: MonteCarloSimulator | None = None
_scorer: PathScorer | None = None
_mitre_mapper: MITREMapper | None = None
_vuln_scorer: VulnerabilityScorer | None = None


def get_graph_builder() -> AttackGraphBuilder:
    """Get the graph builder singleton."""
    global _graph_builder
    if _graph_builder is None:
        _graph_builder = AttackGraphBuilder()
    return _graph_builder


def get_path_finder() -> AttackPathFinder:
    """Get the path finder singleton."""
    global _path_finder
    if _path_finder is None:
        _path_finder = AttackPathFinder(mitre_mapper=get_mitre_mapper())
    return _path_finder


def get_simulator() -> MonteCarloSimulator:
    """Get the Monte Carlo simulator singleton."""
    global _simulator
    if _simulator is None:
        _simulator = MonteCarloSimulator()
    return _simulator


def get_scorer() -> PathScorer:
    """Get the path scorer singleton."""
    global _scorer
    if _scorer is None:
        _scorer = PathScorer()
    return _scorer


def get_mitre_mapper() -> MITREMapper:
    """Get the MITRE mapper singleton."""
    global _mitre_mapper
    if _mitre_mapper is None:
        _mitre_mapper = MITREMapper()
    return _mitre_mapper


def get_vulnerability_scorer() -> VulnerabilityScorer:
    """Get the vulnerability scorer singleton."""
    global _vuln_scorer
    if _vuln_scorer is None:
        _vuln_scorer = VulnerabilityScorer()
    return _vuln_scorer
