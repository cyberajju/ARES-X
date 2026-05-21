"""Attack path scoring service."""

from app.models.attack_path import AttackPath
from app.models.graph import AttackGraph


class PathScorer:
    """Scores and prioritizes attack paths based on probability and impact."""

    def calculate_path_probability(self, path: AttackPath) -> float:
        """Calculate the overall probability of a path being exploited.

        Uses the product of individual step probabilities.
        """
        if not path.steps:
            return 0.0

        probability = 1.0
        for step in path.steps:
            probability *= step.probability

        return probability

    def calculate_path_impact(self, path: AttackPath, graph: AttackGraph) -> float:
        """Calculate impact score based on the criticality of target nodes.

        Returns the maximum criticality value among target nodes in the path.
        """
        if not path.steps:
            return 0.0

        max_criticality = 0.0
        for step in path.steps:
            node = graph.nodes.get(step.node_id)
            if node is not None:
                max_criticality = max(max_criticality, node.criticality)

        return max_criticality

    def calculate_combined_risk(self, probability: float, impact: float) -> float:
        """Calculate combined risk score from probability and impact.

        Uses a weighted combination: 0.6 * probability + 0.4 * impact.
        """
        return 0.6 * probability + 0.4 * impact

    def score_path(self, path: AttackPath, graph: AttackGraph) -> AttackPath:
        """Compute and assign scores to an attack path."""
        probability = self.calculate_path_probability(path)
        impact = self.calculate_path_impact(path, graph)
        combined = self.calculate_combined_risk(probability, impact)

        path.exploitability = probability
        path.impact = impact
        path.total_risk_score = combined

        return path

    def prioritize_paths(self, paths: list[AttackPath]) -> list[AttackPath]:
        """Sort paths by total risk score in descending order."""
        return sorted(paths, key=lambda p: p.total_risk_score, reverse=True)

    def calculate_quick_wins(self, paths: list[AttackPath]) -> list[AttackPath]:
        """Identify paths with high probability and easy remediation.

        Quick wins are paths with high exploitability (>0.5) and few steps (<=3).
        """
        quick_wins = [
            p for p in paths if p.exploitability > 0.5 and len(p.steps) <= 3
        ]
        return sorted(quick_wins, key=lambda p: p.exploitability, reverse=True)

    def calculate_high_impact(self, paths: list[AttackPath]) -> list[AttackPath]:
        """Identify paths targeting critical assets (impact > 0.7)."""
        high_impact = [p for p in paths if p.impact > 0.7]
        return sorted(high_impact, key=lambda p: p.impact, reverse=True)
