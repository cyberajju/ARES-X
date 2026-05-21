/// Request handling logic for gRPC service methods.
///
/// Validates incoming requests, calls into graph algorithms,
/// and builds responses. Handles pagination for large result sets.

use tonic::Status;

use crate::graph::algorithms;
use crate::graph::store::InfraGraph;
use crate::graph::types::{NodeId, NodeType};
use crate::server::grpc::proto;

// ---------------------------------------------------------------------------
// Node type conversion helpers
// ---------------------------------------------------------------------------

/// Convert a proto node type integer to internal NodeType.
fn proto_node_type_to_internal(t: i32) -> Option<NodeType> {
    match t {
        1 => Some(NodeType::Server),
        2 => Some(NodeType::Workstation),
        3 => Some(NodeType::Router), // NETWORK_DEVICE maps to Router
        4 => Some(NodeType::Database),
        5 => Some(NodeType::Application),
        6 => Some(NodeType::Identity), // USER maps to Identity
        7 => Some(NodeType::Identity), // SERVICE_ACCOUNT maps to Identity
        8 => Some(NodeType::CloudVM),  // CLOUD_RESOURCE maps to CloudVM
        9 => Some(NodeType::Container),
        10 => Some(NodeType::Identity),
        _ => None,
    }
}

/// Convert internal NodeType to proto integer.
fn internal_node_type_to_proto(t: &NodeType) -> i32 {
    match t {
        NodeType::Server => 1,
        NodeType::Workstation => 2,
        NodeType::Router | NodeType::Switch => 3,
        NodeType::Database => 4,
        NodeType::Application => 5,
        NodeType::Identity => 10,
        NodeType::CloudVM => 8,
        NodeType::Container => 9,
        NodeType::Firewall => 3,
        NodeType::LoadBalancer => 3,
        NodeType::OTController => 5,
        NodeType::OTSensor => 5,
        NodeType::Unknown => 0,
    }
}

/// Convert an internal Node to a proto node.
fn node_to_proto(node: &crate::graph::types::Node) -> proto::ProtoNode {
    proto::ProtoNode {
        id: node.id.0.clone(),
        name: node.label.clone(),
        node_type: internal_node_type_to_proto(&node.node_type),
        properties: node.properties.clone(),
        risk_score: node.criticality,
    }
}

/// Convert an internal Edge to a proto edge.
fn edge_to_proto(edge: &crate::graph::types::Edge) -> proto::ProtoEdge {
    use crate::graph::types::EdgeType;
    let edge_type_int = match &edge.edge_type {
        EdgeType::ConnectsTo => 1,
        EdgeType::DependsOn => 8,
        EdgeType::AuthenticatesTo => 2,
        EdgeType::Contains => 7,
        EdgeType::AccessibleFrom => 1,
        EdgeType::RoutesTo => 4,
        EdgeType::ReplicatesTo => 5,
        EdgeType::BacksUp => 5,
        EdgeType::Monitors => 6,
        EdgeType::Controls => 3,
    };

    proto::ProtoEdge {
        id: edge.id.0.clone(),
        source_id: edge.source.0.clone(),
        target_id: edge.target.0.clone(),
        edge_type: edge_type_int,
        weight: edge.weight,
        properties: edge.properties.clone(),
    }
}

// ---------------------------------------------------------------------------
// Handler implementations
// ---------------------------------------------------------------------------

/// Handle a QueryNodes request: filter nodes by type and risk score.
pub fn handle_query_nodes(
    graph: &InfraGraph,
    request: &proto::QueryNodesRequest,
) -> Result<proto::QueryNodesResponse, Status> {
    let page_size = if request.page_size > 0 {
        request.page_size as usize
    } else {
        100
    };

    // Parse page token as an offset
    let offset: usize = request.page_token.parse().unwrap_or(0);

    // Filter nodes
    let mut matching_nodes: Vec<&crate::graph::types::Node> = graph
        .nodes
        .values()
        .filter(|node| {
            // Filter by type if specified
            if !request.types.is_empty() {
                let node_proto_type = internal_node_type_to_proto(&node.node_type);
                if !request.types.contains(&node_proto_type) {
                    return false;
                }
            }
            // Filter by minimum risk score
            if request.min_risk_score > 0.0 && node.criticality < request.min_risk_score {
                return false;
            }
            // Filter by properties
            for (key, value) in &request.filters {
                match node.properties.get(key) {
                    Some(v) if v == value => {}
                    _ => return false,
                }
            }
            true
        })
        .collect();

    let total_count = matching_nodes.len() as i32;

    // Sort by criticality descending for consistent pagination
    matching_nodes.sort_by(|a, b| {
        b.criticality
            .partial_cmp(&a.criticality)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    // Apply pagination
    let page_nodes: Vec<proto::ProtoNode> = matching_nodes
        .iter()
        .skip(offset)
        .take(page_size)
        .map(|n| node_to_proto(n))
        .collect();

    let next_page_token = if offset + page_size < matching_nodes.len() {
        (offset + page_size).to_string()
    } else {
        String::new()
    };

    Ok(proto::QueryNodesResponse {
        nodes: page_nodes,
        next_page_token,
        total_count,
    })
}

/// Handle a QueryEdges request: filter edges by type and endpoint.
pub fn handle_query_edges(
    graph: &InfraGraph,
    request: &proto::QueryEdgesRequest,
) -> Result<proto::QueryEdgesResponse, Status> {
    let page_size = if request.page_size > 0 {
        request.page_size as usize
    } else {
        100
    };

    let offset: usize = request.page_token.parse().unwrap_or(0);

    let matching_edges: Vec<&crate::graph::types::Edge> = graph
        .edges
        .values()
        .filter(|edge| {
            // Filter by source if specified
            if !request.source_id.is_empty() && edge.source.0 != request.source_id {
                return false;
            }
            // Filter by target if specified
            if !request.target_id.is_empty() && edge.target.0 != request.target_id {
                return false;
            }
            true
        })
        .collect();

    let total_count = matching_edges.len() as i32;

    let page_edges: Vec<proto::ProtoEdge> = matching_edges
        .iter()
        .skip(offset)
        .take(page_size)
        .map(|e| edge_to_proto(e))
        .collect();

    let next_page_token = if offset + page_size < matching_edges.len() {
        (offset + page_size).to_string()
    } else {
        String::new()
    };

    Ok(proto::QueryEdgesResponse {
        edges: page_edges,
        next_page_token,
        total_count,
    })
}

/// Handle a FindPaths request: discover paths between two nodes.
pub fn handle_find_paths(
    graph: &InfraGraph,
    request: &proto::FindPathsRequest,
) -> Result<proto::FindPathsResponse, Status> {
    // Validate request
    if request.source_id.is_empty() {
        return Err(Status::invalid_argument("source_id is required"));
    }
    if request.target_id.is_empty() {
        return Err(Status::invalid_argument("target_id is required"));
    }

    let source = NodeId::new(&request.source_id);
    let target = NodeId::new(&request.target_id);
    let max_depth = if request.max_depth > 0 {
        request.max_depth as usize
    } else {
        10
    };
    let max_paths = if request.max_paths > 0 {
        request.max_paths as usize
    } else {
        20
    };

    // Find all paths
    let paths = algorithms::find_all_paths(graph, &source, &target, max_depth);
    let total_found = paths.len() as i32;

    // Convert to proto, limiting to max_paths
    let proto_paths: Vec<proto::ProtoPath> = paths
        .iter()
        .take(max_paths)
        .map(|path| {
            let nodes: Vec<proto::ProtoNode> = path
                .iter()
                .filter_map(|nid| graph.get_node(nid))
                .map(|n| node_to_proto(n))
                .collect();

            // Collect edges along the path
            let mut edges = Vec::new();
            let mut total_weight = 0.0;
            for window in path.windows(2) {
                if let Some(edge_ids) = graph.adjacency.get(&window[0]) {
                    for eid in edge_ids {
                        if let Some(edge) = graph.edges.get(eid) {
                            if (edge.source == window[0] && edge.target == window[1])
                                || (edge.bidirectional
                                    && edge.target == window[0]
                                    && edge.source == window[1])
                            {
                                total_weight += edge.weight;
                                edges.push(edge_to_proto(edge));
                                break;
                            }
                        }
                    }
                }
            }

            proto::ProtoPath {
                hop_count: (path.len() as i32) - 1,
                nodes,
                edges,
                total_weight,
            }
        })
        .collect();

    Ok(proto::FindPathsResponse {
        paths: proto_paths,
        total_paths_found: total_found,
    })
}

/// Handle a ComputeBlastRadius request.
pub fn handle_compute_blast_radius(
    graph: &InfraGraph,
    request: &proto::ComputeBlastRadiusRequest,
) -> Result<proto::BlastRadiusResult, Status> {
    if request.node_id.is_empty() {
        return Err(Status::invalid_argument("node_id is required"));
    }

    let node_id = NodeId::new(&request.node_id);
    let max_depth = if request.max_depth > 0 {
        request.max_depth as usize
    } else {
        5
    };

    let result = algorithms::compute_blast_radius(graph, &node_id, max_depth)
        .map_err(|e| {
            let (_code, msg) = e.to_grpc_status();
            Status::internal(msg)
        })?;

    // Build affected_by_type map
    let mut affected_by_type: std::collections::HashMap<String, i32> =
        std::collections::HashMap::new();
    let affected_nodes: Vec<proto::ProtoNode> = result
        .affected_nodes
        .iter()
        .filter_map(|nid| graph.get_node(nid))
        .map(|n| {
            let type_name = format!("{}", n.node_type);
            *affected_by_type.entry(type_name).or_insert(0) += 1;
            node_to_proto(n)
        })
        .collect();

    Ok(proto::BlastRadiusResult {
        origin_id: request.node_id.clone(),
        affected_nodes,
        traversed_edges: Vec::new(), // Simplified: not tracking individual edges in BFS
        total_affected: result.affected_nodes.len() as i32,
        aggregate_risk_score: result.severity,
        affected_by_type,
    })
}

/// Handle a GetCriticalNodes request.
pub fn handle_get_critical_nodes(
    graph: &InfraGraph,
    request: &proto::GetCriticalNodesRequest,
) -> Result<proto::GetCriticalNodesResponse, Status> {
    let top_n = if request.top_n > 0 {
        request.top_n as usize
    } else {
        10
    };

    let critical = algorithms::identify_critical_nodes(graph, top_n);

    let critical_nodes: Vec<proto::ProtoCriticalNode> = critical
        .iter()
        .filter_map(|(node_id, score)| {
            let node = graph.get_node(node_id)?;
            let incoming = graph
                .reverse_adjacency
                .get(node_id)
                .map(|v| v.len() as i32)
                .unwrap_or(0);
            let outgoing = graph
                .adjacency
                .get(node_id)
                .map(|v| v.len() as i32)
                .unwrap_or(0);

            Some(proto::ProtoCriticalNode {
                node: Some(node_to_proto(node)),
                criticality_score: *score,
                incoming_paths: incoming,
                outgoing_paths: outgoing,
                betweenness_centrality: *score,
            })
        })
        .collect();

    Ok(proto::GetCriticalNodesResponse { critical_nodes })
}
