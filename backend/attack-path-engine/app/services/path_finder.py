"""Attack path finding algorithms."""

import uuid
from datetime import datetime, timezone

from app.models.attack_path import AttackPath, PathStep
from app.models.graph import AttackGraph
from app.services.mitre_mapping import MITREMapper


class AttackPathFinder:
    """Finds viable attack paths through an attack graph."""

    def __init__(self, mitre_mapper: MITREMapper | None = None):
        """Initialize the path finder with an optional MITRE mapper."""
        self.mitre_mapper = mitre_mapper or MITREMapper()
        self.min_probability_threshold = 0.01

    def find_paths(
        self,
        graph: AttackGraph,
        entry_points: list[str],
        targets: list[str],
        max_depth: int = 10,
        include_techniques: bool = True,
    ) -> list[AttackPath]:
        """Find all viable attack paths from entry points to targets.

        Uses DFS with pruning: skips paths where cumulative probability
        drops below the threshold.
        """
        all_paths: list[AttackPath] = []

        for entry in entry_points:
            if entry not in graph.nodes:
                continue
            for target in targets:
                if target not in graph.nodes:
                    continue
                if entry == target:
                    continue

                paths = self._dfs_find_paths(
                    graph, entry, target, max_depth, include_techniques
                )
                all_paths.extend(paths)

        # Deduplicate similar paths
        all_paths = self._deduplicate_paths(all_paths)

        return all_paths

    def _dfs_find_paths(
        self,
        graph: AttackGraph,
        start: str,
        target: str,
        max_depth: int,
        include_techniques: bool,
    ) -> list[AttackPath]:
        """Depth-first search for paths from start to target."""
        results: list[AttackPath] = []
        stack: list[tuple[str, list[str], float]] = [(start, [start], 1.0)]

        while stack:
            current, path_nodes, cumulative_prob = stack.pop()

            if current == target and len(path_nodes) > 1:
                # Build AttackPath from the node sequence
                attack_path = self._build_path(
                    graph, path_nodes, cumulative_prob, include_techniques
                )
                results.append(attack_path)
                continue

            if len(path_nodes) >= max_depth:
                continue

            # Prune low-probability paths
            if cumulative_prob < self.min_probability_threshold:
                continue

            # Explore neighbors
            for edge in graph.edges:
                if edge.source != current:
                    continue
                next_node = edge.target
                if next_node in path_nodes:
                    continue  # Avoid cycles

                new_prob = cumulative_prob * edge.probability
                stack.append((next_node, path_nodes + [next_node], new_prob))

        return results

    def _build_path(
        self,
        graph: AttackGraph,
        node_ids: list[str],
        final_probability: float,
        include_techniques: bool,
    ) -> AttackPath:
        """Construct an AttackPath from a sequence of node IDs."""
        steps: list[PathStep] = []
        cumulative = 1.0

        for i, node_id in enumerate(node_ids):
            node = graph.nodes.get(node_id)
            if node is None:
                continue

            # Find the edge leading to this node
            step_probability = 1.0
            technique_id = ""
            technique_name = ""

            if i > 0:
                prev_node = node_ids[i - 1]
                for edge in graph.edges:
                    if edge.source == prev_node and edge.target == node_id:
                        step_probability = edge.probability
                        if include_techniques and edge.technique:
                            technique_id = edge.technique
                            technique_name = edge.technique
                        break

                # Assign MITRE technique if not already set
                if include_techniques and not technique_id:
                    techniques = self.mitre_mapper.map_technique_to_asset_type(
                        node.node_type
                    )
                    if techniques:
                        technique_id = techniques[0].id
                        technique_name = techniques[0].name

            cumulative *= step_probability

            steps.append(
                PathStep(
                    node_id=node_id,
                    node_name=node.label,
                    node_type=node.node_type,
                    technique_id=technique_id,
                    technique_name=technique_name,
                    probability=step_probability,
                    cumulative_risk=cumulative,
                )
            )

        entry_node = graph.nodes.get(node_ids[0])
        target_node = graph.nodes.get(node_ids[-1])

        path_name = f"{entry_node.label if entry_node else node_ids[0]} -> {target_node.label if target_node else node_ids[-1]}"

        return AttackPath(
            id=str(uuid.uuid4()),
            name=path_name,
            steps=steps,
            total_risk_score=final_probability,
            exploitability=final_probability,
            impact=target_node.criticality if target_node else 0.0,
            entry_point=node_ids[0],
            target=node_ids[-1],
            created_at=datetime.now(timezone.utc),
        )

    def _deduplicate_paths(self, paths: list[AttackPath]) -> list[AttackPath]:
        """Remove duplicate paths that visit the same set of nodes."""
        seen: set[tuple[str, ...]] = set()
        unique_paths: list[AttackPath] = []

        for path in paths:
            node_tuple = tuple(step.node_id for step in path.steps)
            if node_tuple not in seen:
                seen.add(node_tuple)
                unique_paths.append(path)

        return unique_paths
