"""Attack graph construction from infrastructure topology."""

from app.models.graph import AttackEdge, AttackGraph, AttackNode
from app.models.vulnerability import Vulnerability


class AttackGraphBuilder:
    """Constructs attack graphs from infrastructure topology data."""

    def build_from_infrastructure(
        self,
        nodes: list[dict],
        edges: list[dict],
        vulnerabilities: list[Vulnerability],
    ) -> AttackGraph:
        """Build an attack graph from infrastructure nodes, edges, and known vulnerabilities.

        Converts infrastructure topology into an attack-relevant graph with exploit edges.
        Edge probabilities are derived from CVSS scores, adjusted for network segmentation.
        """
        graph = AttackGraph()

        # Build nodes
        for node_data in nodes:
            node = AttackNode(
                id=node_data.get("id", ""),
                label=node_data.get("name", node_data.get("label", "")),
                node_type=node_data.get("type", "unknown"),
                criticality=node_data.get("criticality", 0.5),
                vulnerabilities=node_data.get("vulnerabilities", []),
                exploit_probability=node_data.get("exploit_probability", 0.0),
            )
            graph.nodes[node.id] = node

        # Build edges from connectivity
        for edge_data in edges:
            source = edge_data.get("source", "")
            target = edge_data.get("target", "")

            base_probability = edge_data.get("probability", 0.5)

            # Adjust for network segmentation
            source_node = graph.nodes.get(source)
            target_node = graph.nodes.get(target)

            if source_node and target_node:
                probability = self._adjust_for_segmentation(
                    base_probability, source_node, target_node, graph
                )
            else:
                probability = base_probability

            edge = AttackEdge(
                source=source,
                target=target,
                technique=edge_data.get("technique", ""),
                probability=probability,
                prerequisites=edge_data.get("prerequisites", []),
            )
            graph.edges.append(edge)

        # Add exploit edges based on vulnerabilities
        self._add_exploit_edges(graph, vulnerabilities)

        return graph

    def _add_exploit_edges(
        self, graph: AttackGraph, vulnerabilities: list[Vulnerability]
    ) -> None:
        """Add edges representing exploit opportunities based on vulnerabilities."""
        vuln_map: dict[str, list[Vulnerability]] = {}
        for vuln in vulnerabilities:
            for product in vuln.affected_products:
                if product not in vuln_map:
                    vuln_map[product] = []
                vuln_map[product].append(vuln)

        for node_id, node in graph.nodes.items():
            for vuln_id in node.vulnerabilities:
                matching_vulns = vuln_map.get(vuln_id, [])
                for vuln in matching_vulns:
                    prob = self._cvss_to_probability(vuln.cvss.base_score)
                    if vuln.exploit_available:
                        prob = min(prob * 1.5, 0.95)
                    if vuln.patch_available:
                        prob *= 0.7

                    node.exploit_probability = max(node.exploit_probability, prob)

    def _adjust_for_segmentation(
        self,
        base_probability: float,
        source: AttackNode,
        target: AttackNode,
        graph: AttackGraph,
    ) -> float:
        """Reduce probability if a firewall exists between source and target."""
        # Check if there is a firewall node that connects to either source or target
        for node in graph.nodes.values():
            if node.node_type == "firewall":
                # Firewall presence reduces lateral movement probability
                for edge in graph.edges:
                    if edge.source == node.id and (
                        edge.target == source.id or edge.target == target.id
                    ):
                        return base_probability * 0.3
                    if edge.target == node.id and (
                        edge.source == source.id or edge.source == target.id
                    ):
                        return base_probability * 0.3
        return base_probability

    def _cvss_to_probability(self, cvss_score: float) -> float:
        """Convert a CVSS score (0-10) to probability (0-1) using a sigmoid curve."""
        import math

        # Sigmoid-like transformation centered around CVSS 5
        return 1.0 / (1.0 + math.exp(-1.0 * (cvss_score - 5.0)))
