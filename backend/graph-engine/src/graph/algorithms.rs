/// Graph algorithms for infrastructure analysis.
///
/// Implements core graph traversal and analysis algorithms using only
/// standard library data structures (BinaryHeap, VecDeque, HashMap, HashSet).
///
/// Key algorithms:
/// - Dijkstra's shortest path (BinaryHeap min-heap)
/// - All-paths DFS with depth limiting
/// - Attack path discovery with risk scoring
/// - Blast radius computation (BFS)
/// - Betweenness centrality approximation
/// - Dependency analysis with cycle detection

use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap, HashSet, VecDeque};

use serde::{Deserialize, Serialize};

use crate::error::GraphError;
use crate::graph::store::InfraGraph;
use crate::graph::types::{EdgeId, EdgeType, NodeId};

// ---------------------------------------------------------------------------
// Dijkstra's Shortest Path
// ---------------------------------------------------------------------------

/// State used in Dijkstra's priority queue.
/// Implements Ord with reverse ordering so BinaryHeap acts as a min-heap.
#[derive(Debug, Clone)]
struct DijkstraState {
    cost: f64,
    node: NodeId,
}

impl PartialEq for DijkstraState {
    fn eq(&self, other: &Self) -> bool {
        self.cost == other.cost
    }
}

impl Eq for DijkstraState {}

impl PartialOrd for DijkstraState {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for DijkstraState {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse ordering for min-heap behavior:
        // smaller cost = higher priority
        other
            .cost
            .partial_cmp(&self.cost)
            .unwrap_or(Ordering::Equal)
    }
}

/// Find the shortest path between two nodes using Dijkstra's algorithm.
///
/// Uses edge weights as costs (inverted: higher weight = easier traversal = lower cost).
/// Returns the path (sequence of NodeIds) and the total path cost.
/// Uses a BinaryHeap with reversed ordering for min-heap behavior.
///
/// # Arguments
/// * `graph` - The infrastructure graph to search
/// * `source` - Starting node ID
/// * `target` - Destination node ID
///
/// # Returns
/// A tuple of (path as Vec<NodeId>, total cost as f64), or a GraphError.
pub fn shortest_path(
    graph: &InfraGraph,
    source: &NodeId,
    target: &NodeId,
) -> Result<(Vec<NodeId>, f64), GraphError> {
    if !graph.nodes.contains_key(source) {
        return Err(GraphError::NodeNotFound(source.to_string()));
    }
    if !graph.nodes.contains_key(target) {
        return Err(GraphError::NodeNotFound(target.to_string()));
    }
    if source == target {
        return Ok((vec![source.clone()], 0.0));
    }

    let mut distances: HashMap<NodeId, f64> = HashMap::new();
    let mut predecessors: HashMap<NodeId, NodeId> = HashMap::new();
    let mut heap = BinaryHeap::new();

    // Initialize source distance
    distances.insert(source.clone(), 0.0);
    heap.push(DijkstraState {
        cost: 0.0,
        node: source.clone(),
    });

    while let Some(DijkstraState { cost, node }) = heap.pop() {
        // Early termination if we reached the target
        if &node == target {
            break;
        }

        // Skip if we already found a better path to this node
        if let Some(&best) = distances.get(&node) {
            if cost > best {
                continue;
            }
        }

        // Explore outgoing edges
        if let Some(edge_ids) = graph.adjacency.get(&node) {
            for edge_id in edge_ids {
                if let Some(edge) = graph.edges.get(edge_id) {
                    // Determine the neighbor node
                    let neighbor = if edge.source == node {
                        &edge.target
                    } else {
                        &edge.source
                    };

                    // Convert weight to cost: higher weight = easier = lower cost
                    // Weight of 0 means impassable (very high cost)
                    let edge_cost = if edge.weight > 0.0 {
                        1.0 / edge.weight
                    } else {
                        f64::MAX / 2.0
                    };

                    let new_cost = cost + edge_cost;
                    let current_best = distances.get(neighbor).copied().unwrap_or(f64::MAX);

                    if new_cost < current_best {
                        distances.insert(neighbor.clone(), new_cost);
                        predecessors.insert(neighbor.clone(), node.clone());
                        heap.push(DijkstraState {
                            cost: new_cost,
                            node: neighbor.clone(),
                        });
                    }
                }
            }
        }
    }

    // Reconstruct path from target back to source
    if !predecessors.contains_key(target) {
        return Err(GraphError::PathNotFound {
            source: source.to_string(),
            target: target.to_string(),
        });
    }

    let mut path = Vec::new();
    let mut current = target.clone();
    while &current != source {
        path.push(current.clone());
        current = predecessors
            .get(&current)
            .ok_or_else(|| GraphError::PathNotFound {
                source: source.to_string(),
                target: target.to_string(),
            })?
            .clone();
    }
    path.push(source.clone());
    path.reverse();

    let total_cost = distances.get(target).copied().unwrap_or(0.0);
    Ok((path, total_cost))
}

// ---------------------------------------------------------------------------
// All Paths (DFS with depth limit)
// ---------------------------------------------------------------------------

/// Find all paths between two nodes up to a maximum depth.
///
/// Uses recursive DFS with backtracking and a visited set to avoid cycles.
/// Results are sorted by path length (shortest first).
///
/// # Arguments
/// * `graph` - The infrastructure graph to search
/// * `source` - Starting node ID
/// * `target` - Destination node ID
/// * `max_depth` - Maximum path length (number of edges)
///
/// # Returns
/// A vector of paths, each being a sequence of NodeIds, sorted by length.
pub fn find_all_paths(
    graph: &InfraGraph,
    source: &NodeId,
    target: &NodeId,
    max_depth: usize,
) -> Vec<Vec<NodeId>> {
    if !graph.nodes.contains_key(source) || !graph.nodes.contains_key(target) {
        return Vec::new();
    }
    if source == target {
        return vec![vec![source.clone()]];
    }

    let mut all_paths = Vec::new();
    let mut current_path = vec![source.clone()];
    let mut visited = HashSet::new();
    visited.insert(source.clone());

    dfs_all_paths(
        graph,
        source,
        target,
        max_depth,
        &mut current_path,
        &mut visited,
        &mut all_paths,
    );

    // Sort by path length (shortest first)
    all_paths.sort_by_key(|path| path.len());
    all_paths
}

/// Recursive DFS helper for finding all paths.
fn dfs_all_paths(
    graph: &InfraGraph,
    current: &NodeId,
    target: &NodeId,
    max_depth: usize,
    current_path: &mut Vec<NodeId>,
    visited: &mut HashSet<NodeId>,
    all_paths: &mut Vec<Vec<NodeId>>,
) {
    // current_path already includes `current`; edges traversed = len - 1
    if current_path.len() - 1 >= max_depth {
        return;
    }

    if let Some(edge_ids) = graph.adjacency.get(current) {
        for edge_id in edge_ids {
            if let Some(edge) = graph.edges.get(edge_id) {
                let neighbor = if edge.source == *current {
                    &edge.target
                } else {
                    &edge.source
                };

                if neighbor == target {
                    // Found a path to target
                    let mut path = current_path.clone();
                    path.push(target.clone());
                    all_paths.push(path);
                } else if !visited.contains(neighbor) {
                    // Continue DFS deeper
                    visited.insert(neighbor.clone());
                    current_path.push(neighbor.clone());
                    dfs_all_paths(
                        graph, neighbor, target, max_depth, current_path, visited, all_paths,
                    );
                    current_path.pop();
                    visited.remove(neighbor);
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Attack Path Discovery
// ---------------------------------------------------------------------------

/// A discovered attack path through the infrastructure graph.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AttackPath {
    /// Sequence of nodes traversed.
    pub nodes: Vec<NodeId>,
    /// Sequence of edges traversed.
    pub edges: Vec<EdgeId>,
    /// Total risk score for this path.
    pub total_risk: f64,
    /// Exploitability score (product of edge weights along the path).
    pub exploitability: f64,
}

/// Discover attack paths from entry points to target nodes.
///
/// For each combination of entry point and target, finds viable paths
/// and scores them based on edge weights and node criticalities.
/// Results are sorted by total_risk in descending order (most dangerous first).
///
/// # Arguments
/// * `graph` - The infrastructure graph
/// * `entry_points` - Possible attacker entry nodes
/// * `targets` - High-value target nodes
/// * `max_depth` - Maximum path length to consider
///
/// # Returns
/// A vector of AttackPaths sorted by total_risk descending.
pub fn discover_attack_paths(
    graph: &InfraGraph,
    entry_points: &[NodeId],
    targets: &[NodeId],
    max_depth: usize,
) -> Vec<AttackPath> {
    let mut attack_paths = Vec::new();

    for entry in entry_points {
        for target in targets {
            if entry == target {
                continue;
            }
            let paths = find_all_paths(graph, entry, target, max_depth);
            for path in paths {
                if let Some(attack_path) = build_attack_path(graph, &path) {
                    attack_paths.push(attack_path);
                }
            }
        }
    }

    // Sort by total_risk descending (most dangerous first)
    attack_paths.sort_by(|a, b| {
        b.total_risk
            .partial_cmp(&a.total_risk)
            .unwrap_or(Ordering::Equal)
    });

    attack_paths
}

/// Build and score an attack path from a sequence of nodes.
fn build_attack_path(graph: &InfraGraph, path: &[NodeId]) -> Option<AttackPath> {
    if path.len() < 2 {
        return None;
    }

    let mut edges_used = Vec::new();
    let mut exploitability = 1.0;

    // Walk the path and find connecting edges
    for window in path.windows(2) {
        let from = &window[0];
        let to = &window[1];

        // Find an edge connecting from -> to
        let edge = graph.adjacency.get(from).and_then(|edge_ids| {
            edge_ids.iter().find_map(|eid| {
                let e = graph.edges.get(eid)?;
                if (e.source == *from && e.target == *to)
                    || (e.bidirectional && e.target == *from && e.source == *to)
                {
                    Some(e)
                } else {
                    None
                }
            })
        });

        if let Some(edge) = edge {
            edges_used.push(edge.id.clone());
            exploitability *= edge.weight;
        } else {
            // No direct edge found between consecutive nodes - path is invalid
            return None;
        }
    }

    // Impact = maximum criticality among all nodes on the path
    let impact: f64 = path
        .iter()
        .filter_map(|nid| graph.nodes.get(nid))
        .map(|n| n.criticality)
        .fold(0.0_f64, f64::max);

    // Path length factor: shorter paths are more dangerous
    let path_length_factor = 1.0 / path.len() as f64;

    let total_risk = exploitability * impact * path_length_factor;

    Some(AttackPath {
        nodes: path.to_vec(),
        edges: edges_used,
        total_risk,
        exploitability,
    })
}

// ---------------------------------------------------------------------------
// Blast Radius Computation
// ---------------------------------------------------------------------------

/// Result of a blast radius computation from a compromised node.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BlastRadius {
    /// All nodes affected by the compromise (excluding the origin).
    pub affected_nodes: Vec<NodeId>,
    /// Distance (in hops) from the compromised node to each affected node.
    pub hop_distances: HashMap<NodeId, usize>,
    /// Sum of criticality scores of all affected nodes.
    pub total_criticality: f64,
    /// Severity score: sum of (criticality / hop_distance) for each affected node.
    pub severity: f64,
}

/// Compute the blast radius from a compromised node using BFS.
///
/// Traverses outgoing edges from the compromised node up to max_hops,
/// computing the set of affected nodes and severity based on criticality
/// weighted inversely by distance.
///
/// # Arguments
/// * `graph` - The infrastructure graph
/// * `compromised` - The initially compromised node
/// * `max_hops` - Maximum traversal depth
///
/// # Returns
/// BlastRadius containing affected nodes, distances, and severity scores.
pub fn compute_blast_radius(
    graph: &InfraGraph,
    compromised: &NodeId,
    max_hops: usize,
) -> Result<BlastRadius, GraphError> {
    if !graph.nodes.contains_key(compromised) {
        return Err(GraphError::NodeNotFound(compromised.to_string()));
    }

    let mut affected_nodes = Vec::new();
    let mut hop_distances: HashMap<NodeId, usize> = HashMap::new();
    let mut visited: HashSet<NodeId> = HashSet::new();
    let mut queue: VecDeque<(NodeId, usize)> = VecDeque::new();

    visited.insert(compromised.clone());
    queue.push_back((compromised.clone(), 0));

    while let Some((current, hops)) = queue.pop_front() {
        if hops > 0 {
            affected_nodes.push(current.clone());
            hop_distances.insert(current.clone(), hops);
        }

        if hops >= max_hops {
            continue;
        }

        // Traverse outgoing edges from current node
        if let Some(edge_ids) = graph.adjacency.get(&current) {
            for edge_id in edge_ids {
                if let Some(edge) = graph.edges.get(edge_id) {
                    let neighbor = if edge.source == current {
                        &edge.target
                    } else {
                        &edge.source
                    };

                    if !visited.contains(neighbor) {
                        visited.insert(neighbor.clone());
                        queue.push_back((neighbor.clone(), hops + 1));
                    }
                }
            }
        }
    }

    // Compute total criticality and severity
    let mut total_criticality = 0.0;
    let mut severity = 0.0;

    for node_id in &affected_nodes {
        if let Some(node) = graph.nodes.get(node_id) {
            total_criticality += node.criticality;
            if let Some(&hops) = hop_distances.get(node_id) {
                if hops > 0 {
                    severity += node.criticality / hops as f64;
                }
            }
        }
    }

    Ok(BlastRadius {
        affected_nodes,
        hop_distances,
        total_criticality,
        severity,
    })
}

// ---------------------------------------------------------------------------
// Critical Node Identification (Betweenness Centrality)
// ---------------------------------------------------------------------------

/// Identify the most critical nodes using approximate betweenness centrality.
///
/// For a sample of node pairs, computes shortest paths and counts how often
/// each node appears as an intermediate node on shortest paths. Combines
/// the betweenness score with the node's own criticality.
///
/// # Arguments
/// * `graph` - The infrastructure graph
/// * `top_n` - Number of top critical nodes to return
///
/// # Returns
/// Vector of (NodeId, combined_score) tuples sorted by score descending.
pub fn identify_critical_nodes(graph: &InfraGraph, top_n: usize) -> Vec<(NodeId, f64)> {
    let node_ids: Vec<NodeId> = graph.nodes.keys().cloned().collect();
    let n = node_ids.len();

    if n == 0 {
        return Vec::new();
    }

    let mut betweenness: HashMap<NodeId, f64> = HashMap::new();
    for id in &node_ids {
        betweenness.insert(id.clone(), 0.0);
    }

    // Determine pairs to sample: all pairs for small graphs, deterministic sample for large
    let max_pairs: usize = 500;
    let pairs: Vec<(NodeId, NodeId)> = if n * (n - 1) <= max_pairs * 2 {
        // Use all pairs for small graphs
        let mut all_pairs = Vec::new();
        for s in &node_ids {
            for t in &node_ids {
                if s != t {
                    all_pairs.push((s.clone(), t.clone()));
                }
            }
        }
        all_pairs
    } else {
        // Deterministic sampling using stride
        let total_pairs = n * (n - 1);
        let stride = total_pairs / max_pairs;
        let mut sampled = Vec::new();
        let mut idx = 0usize;
        'outer: for s in &node_ids {
            for t in &node_ids {
                if s == t {
                    continue;
                }
                if idx % stride == 0 {
                    sampled.push((s.clone(), t.clone()));
                    if sampled.len() >= max_pairs {
                        break 'outer;
                    }
                }
                idx += 1;
            }
        }
        sampled
    };

    let num_pairs = pairs.len() as f64;

    // For each sampled pair, find shortest path and credit intermediate nodes
    for (source, target) in &pairs {
        if let Ok((path, _)) = shortest_path(graph, source, target) {
            // Credit intermediate nodes (skip source and target)
            if path.len() > 2 {
                for node_id in &path[1..path.len() - 1] {
                    if let Some(count) = betweenness.get_mut(node_id) {
                        *count += 1.0;
                    }
                }
            }
        }
    }

    // Normalize betweenness by number of pairs sampled
    if num_pairs > 0.0 {
        for val in betweenness.values_mut() {
            *val /= num_pairs;
        }
    }

    // Combine betweenness centrality with node criticality
    let mut scores: Vec<(NodeId, f64)> = node_ids
        .iter()
        .map(|id| {
            let bc = betweenness.get(id).copied().unwrap_or(0.0);
            let criticality = graph
                .nodes
                .get(id)
                .map(|n| n.criticality)
                .unwrap_or(0.0);
            // Combined score: weighted combination of betweenness and criticality
            let score = 0.6 * bc + 0.4 * criticality;
            (id.clone(), score)
        })
        .collect();

    // Sort by score descending
    scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal));
    scores.truncate(top_n);
    scores
}

// ---------------------------------------------------------------------------
// Dependency Analysis
// ---------------------------------------------------------------------------

/// Result of dependency analysis for a node.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DependencyAnalysis {
    /// Direct dependencies (one hop via DependsOn edges).
    pub direct_deps: Vec<NodeId>,
    /// All transitive dependencies (full transitive closure).
    pub transitive_deps: Vec<NodeId>,
    /// Nodes that depend on this node (reverse dependencies).
    pub dependents: Vec<NodeId>,
    /// Circular dependency chains involving this node.
    pub circular_deps: Vec<Vec<NodeId>>,
    /// Maximum dependency chain depth.
    pub depth: usize,
}

/// Analyze dependencies for a given node.
///
/// Walks DependsOn edges to find direct and transitive dependencies,
/// identifies reverse dependents, and detects circular dependencies
/// using DFS with node coloring (white/gray/black).
///
/// # Arguments
/// * `graph` - The infrastructure graph
/// * `node` - The node to analyze
///
/// # Returns
/// DependencyAnalysis with all dependency information, or an error if the node is not found.
pub fn analyze_dependencies(
    graph: &InfraGraph,
    node: &NodeId,
) -> Result<DependencyAnalysis, GraphError> {
    if !graph.nodes.contains_key(node) {
        return Err(GraphError::NodeNotFound(node.to_string()));
    }

    // Find direct dependencies (outgoing DependsOn edges from this node)
    let direct_deps = get_dependency_targets(graph, node);

    // Find all transitive dependencies via BFS on DependsOn edges
    let (transitive_deps, depth) = find_transitive_deps(graph, node);

    // Find dependents (nodes that depend on this node via incoming DependsOn edges)
    let dependents = find_dependents(graph, node);

    // Detect circular dependencies using DFS coloring
    let circular_deps = detect_circular_deps(graph, node);

    Ok(DependencyAnalysis {
        direct_deps,
        transitive_deps,
        dependents,
        circular_deps,
        depth,
    })
}

/// Get direct dependency targets from a node (outgoing DependsOn edges).
fn get_dependency_targets(graph: &InfraGraph, node: &NodeId) -> Vec<NodeId> {
    graph
        .adjacency
        .get(node)
        .map(|edge_ids| {
            edge_ids
                .iter()
                .filter_map(|eid| graph.edges.get(eid))
                .filter(|edge| edge.edge_type == EdgeType::DependsOn && edge.source == *node)
                .map(|edge| edge.target.clone())
                .collect()
        })
        .unwrap_or_default()
}

/// Find all transitive dependencies using BFS on DependsOn edges.
/// Returns (all transitive deps excluding the start node, max depth).
fn find_transitive_deps(graph: &InfraGraph, start: &NodeId) -> (Vec<NodeId>, usize) {
    let mut visited: HashSet<NodeId> = HashSet::new();
    let mut queue: VecDeque<(NodeId, usize)> = VecDeque::new();
    let mut all_deps = Vec::new();
    let mut max_depth: usize = 0;

    // Seed with direct deps
    for dep in get_dependency_targets(graph, start) {
        if !visited.contains(&dep) {
            visited.insert(dep.clone());
            queue.push_back((dep, 1));
        }
    }

    while let Some((current, depth)) = queue.pop_front() {
        all_deps.push(current.clone());
        if depth > max_depth {
            max_depth = depth;
        }

        // Continue walking DependsOn edges from current
        for next_dep in get_dependency_targets(graph, &current) {
            if !visited.contains(&next_dep) {
                visited.insert(next_dep.clone());
                queue.push_back((next_dep, depth + 1));
            }
        }
    }

    (all_deps, max_depth)
}

/// Find all nodes that depend on the given node (incoming DependsOn edges).
fn find_dependents(graph: &InfraGraph, node: &NodeId) -> Vec<NodeId> {
    graph
        .reverse_adjacency
        .get(node)
        .map(|edge_ids| {
            edge_ids
                .iter()
                .filter_map(|eid| graph.edges.get(eid))
                .filter(|edge| edge.edge_type == EdgeType::DependsOn && edge.target == *node)
                .map(|edge| edge.source.clone())
                .collect()
        })
        .unwrap_or_default()
}

/// Node coloring for DFS cycle detection.
#[derive(Clone, Copy, PartialEq, Eq)]
enum DfsColor {
    /// Not yet visited.
    White,
    /// Currently in the DFS stack (part of active exploration path).
    Gray,
    /// Fully explored, no longer on the stack.
    Black,
}

/// Detect circular dependencies involving the given start node.
///
/// Uses DFS with three-color marking:
/// - White: unvisited
/// - Gray: currently being explored (on the DFS stack)
/// - Black: fully explored
///
/// A back-edge to a gray node indicates a cycle.
fn detect_circular_deps(graph: &InfraGraph, start: &NodeId) -> Vec<Vec<NodeId>> {
    let mut colors: HashMap<NodeId, DfsColor> = HashMap::new();
    let mut cycles: Vec<Vec<NodeId>> = Vec::new();
    let mut path: Vec<NodeId> = Vec::new();

    // First, find all nodes reachable via DependsOn edges from start
    let mut reachable: HashSet<NodeId> = HashSet::new();
    let mut bfs_queue: VecDeque<NodeId> = VecDeque::new();
    bfs_queue.push_back(start.clone());
    reachable.insert(start.clone());

    while let Some(current) = bfs_queue.pop_front() {
        for dep in get_dependency_targets(graph, &current) {
            if !reachable.contains(&dep) {
                reachable.insert(dep.clone());
                bfs_queue.push_back(dep);
            }
        }
    }

    // Initialize all reachable nodes as white
    for node_id in &reachable {
        colors.insert(node_id.clone(), DfsColor::White);
    }

    // Run DFS from start
    dfs_cycle_detect(graph, start, &mut colors, &mut path, &mut cycles);

    // Only keep cycles that include the start node
    cycles
        .into_iter()
        .filter(|cycle| cycle.contains(start))
        .collect()
}

/// Recursive DFS cycle detection using node coloring.
fn dfs_cycle_detect(
    graph: &InfraGraph,
    current: &NodeId,
    colors: &mut HashMap<NodeId, DfsColor>,
    path: &mut Vec<NodeId>,
    cycles: &mut Vec<Vec<NodeId>>,
) {
    colors.insert(current.clone(), DfsColor::Gray);
    path.push(current.clone());

    for dep in get_dependency_targets(graph, current) {
        match colors.get(&dep).copied() {
            Some(DfsColor::Gray) => {
                // Found a back-edge: extract the cycle from path
                if let Some(pos) = path.iter().position(|n| *n == dep) {
                    let cycle: Vec<NodeId> = path[pos..].to_vec();
                    cycles.push(cycle);
                }
            }
            Some(DfsColor::White) => {
                dfs_cycle_detect(graph, &dep, colors, path, cycles);
            }
            _ => {
                // Black or missing: already fully explored, skip
            }
        }
    }

    path.pop();
    colors.insert(current.clone(), DfsColor::Black);
}
