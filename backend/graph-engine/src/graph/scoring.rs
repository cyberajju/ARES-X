/// Risk scoring utilities for graph paths and nodes.
///
/// Provides path-level risk assessment combining edge exploitability,
/// node criticality, and path length factors.

use serde::{Deserialize, Serialize};

use crate::graph::store::InfraGraph;
use crate::graph::types::NodeId;

/// Risk score breakdown for a single path through the graph.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PathRiskScore {
    /// Combined total risk score.
    pub total_risk: f64,
    /// Exploitability: product of edge weights along the path (0.0 to 1.0).
    /// Higher = easier to exploit.
    pub exploitability: f64,
    /// Impact: maximum criticality of any node on the path.
    pub impact: f64,
    /// Path length factor: 1.0 / path.len(). Shorter paths are more dangerous.
    pub path_length_factor: f64,
}

/// Score a path through the graph for risk assessment.
///
/// Computes:
/// - exploitability = product of edge weights along the path
/// - impact = max criticality of nodes on the path
/// - path_length_factor = 1.0 / path length (shorter = more dangerous)
/// - total_risk = exploitability * impact * path_length_factor
///
/// # Arguments
/// * `graph` - The infrastructure graph
/// * `path` - Sequence of node IDs representing the path
///
/// # Returns
/// A PathRiskScore with the computed metrics.
pub fn score_path(graph: &InfraGraph, path: &[NodeId]) -> PathRiskScore {
    if path.is_empty() {
        return PathRiskScore {
            total_risk: 0.0,
            exploitability: 0.0,
            impact: 0.0,
            path_length_factor: 0.0,
        };
    }

    if path.len() == 1 {
        let impact = graph
            .nodes
            .get(&path[0])
            .map(|n| n.criticality)
            .unwrap_or(0.0);
        return PathRiskScore {
            total_risk: impact,
            exploitability: 1.0,
            impact,
            path_length_factor: 1.0,
        };
    }

    // Compute exploitability as product of edge weights along the path
    let mut exploitability = 1.0;
    for window in path.windows(2) {
        let from = &window[0];
        let to = &window[1];

        let edge_weight = graph
            .adjacency
            .get(from)
            .and_then(|edge_ids| {
                edge_ids.iter().find_map(|eid| {
                    let e = graph.edges.get(eid)?;
                    if (e.source == *from && e.target == *to)
                        || (e.bidirectional && e.target == *from && e.source == *to)
                    {
                        Some(e.weight)
                    } else {
                        None
                    }
                })
            })
            .unwrap_or(0.0);

        exploitability *= edge_weight;
    }

    // Impact = max criticality of any node on the path
    let impact: f64 = path
        .iter()
        .filter_map(|nid| graph.nodes.get(nid))
        .map(|n| n.criticality)
        .fold(0.0_f64, f64::max);

    // Shorter paths are more dangerous
    let path_length_factor = 1.0 / path.len() as f64;

    let total_risk = exploitability * impact * path_length_factor;

    PathRiskScore {
        total_risk,
        exploitability,
        impact,
        path_length_factor,
    }
}

/// Compute an aggregate severity score for a set of affected nodes.
///
/// Uses criticality weighted by inverse distance from the origin.
///
/// # Arguments
/// * `graph` - The infrastructure graph
/// * `affected` - Pairs of (NodeId, hop_distance)
///
/// # Returns
/// Aggregate severity score.
pub fn compute_severity(graph: &InfraGraph, affected: &[(NodeId, usize)]) -> f64 {
    affected
        .iter()
        .filter_map(|(node_id, hops)| {
            let node = graph.nodes.get(node_id)?;
            if *hops > 0 {
                Some(node.criticality / *hops as f64)
            } else {
                Some(node.criticality)
            }
        })
        .sum()
}
