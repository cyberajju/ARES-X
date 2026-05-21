/// In-memory graph data structure with adjacency list representation.
///
/// The `InfraGraph` stores nodes and edges with efficient lookup by ID,
/// outgoing adjacency (forward edges), and incoming adjacency (reverse edges).

use std::collections::HashMap;

use crate::error::GraphError;
use crate::graph::types::{Edge, EdgeId, EdgeType, Node, NodeId, NodeType};

/// In-memory infrastructure graph with adjacency lists for efficient traversal.
#[derive(Debug, Clone)]
pub struct InfraGraph {
    /// All nodes indexed by their ID.
    pub nodes: HashMap<NodeId, Node>,
    /// Outgoing edges from each node (node -> list of edge IDs).
    pub adjacency: HashMap<NodeId, Vec<EdgeId>>,
    /// Incoming edges to each node (node -> list of edge IDs).
    pub reverse_adjacency: HashMap<NodeId, Vec<EdgeId>>,
    /// All edges indexed by their ID.
    pub edges: HashMap<EdgeId, Edge>,
}

impl InfraGraph {
    /// Create a new empty graph.
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            adjacency: HashMap::new(),
            reverse_adjacency: HashMap::new(),
            edges: HashMap::new(),
        }
    }

    /// Add a node to the graph.
    ///
    /// Returns an error if a node with the same ID already exists.
    pub fn add_node(&mut self, node: Node) -> Result<(), GraphError> {
        if self.nodes.contains_key(&node.id) {
            return Err(GraphError::DuplicateNode(node.id.to_string()));
        }
        let id = node.id.clone();
        self.nodes.insert(id.clone(), node);
        self.adjacency.entry(id.clone()).or_default();
        self.reverse_adjacency.entry(id).or_default();
        Ok(())
    }

    /// Remove a node and all its connected edges from the graph.
    ///
    /// Returns the removed node, or an error if the node was not found.
    pub fn remove_node(&mut self, id: &NodeId) -> Result<Node, GraphError> {
        let node = self
            .nodes
            .remove(id)
            .ok_or_else(|| GraphError::NodeNotFound(id.to_string()))?;

        // Collect edges to remove (outgoing)
        let outgoing_edges: Vec<EdgeId> = self
            .adjacency
            .remove(id)
            .unwrap_or_default();

        // Collect edges to remove (incoming)
        let incoming_edges: Vec<EdgeId> = self
            .reverse_adjacency
            .remove(id)
            .unwrap_or_default();

        // Remove outgoing edges and clean up reverse adjacency
        for edge_id in &outgoing_edges {
            if let Some(edge) = self.edges.remove(edge_id) {
                if let Some(rev_adj) = self.reverse_adjacency.get_mut(&edge.target) {
                    rev_adj.retain(|eid| eid != edge_id);
                }
            }
        }

        // Remove incoming edges and clean up forward adjacency
        for edge_id in &incoming_edges {
            if let Some(edge) = self.edges.remove(edge_id) {
                if let Some(fwd_adj) = self.adjacency.get_mut(&edge.source) {
                    fwd_adj.retain(|eid| eid != edge_id);
                }
            }
        }

        Ok(node)
    }

    /// Get a reference to a node by ID.
    pub fn get_node(&self, id: &NodeId) -> Option<&Node> {
        self.nodes.get(id)
    }

    /// Get a mutable reference to a node by ID.
    pub fn get_node_mut(&mut self, id: &NodeId) -> Option<&mut Node> {
        self.nodes.get_mut(id)
    }

    /// Add an edge to the graph.
    ///
    /// Returns an error if:
    /// - An edge with the same ID already exists
    /// - The source or target node does not exist
    pub fn add_edge(&mut self, edge: Edge) -> Result<(), GraphError> {
        if self.edges.contains_key(&edge.id) {
            return Err(GraphError::DuplicateEdge(edge.id.to_string()));
        }
        if !self.nodes.contains_key(&edge.source) {
            return Err(GraphError::NodeNotFound(edge.source.to_string()));
        }
        if !self.nodes.contains_key(&edge.target) {
            return Err(GraphError::NodeNotFound(edge.target.to_string()));
        }

        let edge_id = edge.id.clone();
        let source = edge.source.clone();
        let target = edge.target.clone();
        let bidirectional = edge.bidirectional;

        self.edges.insert(edge_id.clone(), edge);
        self.adjacency.entry(source.clone()).or_default().push(edge_id.clone());
        self.reverse_adjacency.entry(target.clone()).or_default().push(edge_id.clone());

        // If bidirectional, also add to forward adjacency of target and reverse of source
        if bidirectional {
            self.adjacency.entry(target).or_default().push(edge_id.clone());
            self.reverse_adjacency.entry(source).or_default().push(edge_id);
        }

        Ok(())
    }

    /// Remove an edge from the graph.
    ///
    /// Returns the removed edge, or an error if not found.
    pub fn remove_edge(&mut self, id: &EdgeId) -> Result<Edge, GraphError> {
        let edge = self
            .edges
            .remove(id)
            .ok_or_else(|| GraphError::EdgeNotFound(id.to_string()))?;

        // Remove from forward adjacency
        if let Some(adj) = self.adjacency.get_mut(&edge.source) {
            adj.retain(|eid| eid != id);
        }

        // Remove from reverse adjacency
        if let Some(rev_adj) = self.reverse_adjacency.get_mut(&edge.target) {
            rev_adj.retain(|eid| eid != id);
        }

        // If bidirectional, also clean up the reverse entries
        if edge.bidirectional {
            if let Some(adj) = self.adjacency.get_mut(&edge.target) {
                adj.retain(|eid| eid != id);
            }
            if let Some(rev_adj) = self.reverse_adjacency.get_mut(&edge.source) {
                rev_adj.retain(|eid| eid != id);
            }
        }

        Ok(edge)
    }

    /// Get a reference to an edge by ID.
    pub fn get_edge(&self, id: &EdgeId) -> Option<&Edge> {
        self.edges.get(id)
    }

    /// Get all neighbor nodes reachable via outgoing edges from the given node.
    pub fn get_neighbors(&self, id: &NodeId) -> Vec<&Node> {
        self.adjacency
            .get(id)
            .map(|edge_ids| {
                edge_ids
                    .iter()
                    .filter_map(|eid| self.edges.get(eid))
                    .filter_map(|edge| {
                        // For outgoing edges, the neighbor is the target
                        // unless this is a bidirectional edge where the node is the target
                        if &edge.source == id {
                            self.nodes.get(&edge.target)
                        } else {
                            self.nodes.get(&edge.source)
                        }
                    })
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Get all nodes with incoming edges to the given node.
    pub fn get_incoming(&self, id: &NodeId) -> Vec<&Node> {
        self.reverse_adjacency
            .get(id)
            .map(|edge_ids| {
                edge_ids
                    .iter()
                    .filter_map(|eid| self.edges.get(eid))
                    .filter_map(|edge| {
                        if &edge.target == id {
                            self.nodes.get(&edge.source)
                        } else {
                            self.nodes.get(&edge.target)
                        }
                    })
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Get all outgoing edges from a node.
    pub fn get_edges_from(&self, id: &NodeId) -> Vec<&Edge> {
        self.adjacency
            .get(id)
            .map(|edge_ids| {
                edge_ids
                    .iter()
                    .filter_map(|eid| self.edges.get(eid))
                    .filter(|edge| &edge.source == id)
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Get all incoming edges to a node.
    pub fn get_edges_to(&self, id: &NodeId) -> Vec<&Edge> {
        self.reverse_adjacency
            .get(id)
            .map(|edge_ids| {
                edge_ids
                    .iter()
                    .filter_map(|eid| self.edges.get(eid))
                    .filter(|edge| &edge.target == id)
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Get the total number of nodes.
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Get the total number of edges.
    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }

    /// Get all nodes of a specific type.
    pub fn get_nodes_by_type(&self, node_type: NodeType) -> Vec<&Node> {
        self.nodes
            .values()
            .filter(|n| n.node_type == node_type)
            .collect()
    }

    /// Get all edges of a specific type.
    pub fn get_edges_by_type(&self, edge_type: EdgeType) -> Vec<&Edge> {
        self.edges
            .values()
            .filter(|e| e.edge_type == edge_type)
            .collect()
    }

    /// Extract a subgraph containing only the specified nodes and edges between them.
    pub fn get_subgraph(&self, node_ids: &[NodeId]) -> InfraGraph {
        let mut subgraph = InfraGraph::new();
        let node_set: std::collections::HashSet<&NodeId> = node_ids.iter().collect();

        // Add nodes
        for node_id in node_ids {
            if let Some(node) = self.nodes.get(node_id) {
                let _ = subgraph.add_node(node.clone());
            }
        }

        // Add edges where both source and target are in the subgraph
        for edge in self.edges.values() {
            if node_set.contains(&edge.source) && node_set.contains(&edge.target) {
                let _ = subgraph.add_edge(edge.clone());
            }
        }

        subgraph
    }

    /// Get all node IDs in the graph.
    pub fn node_ids(&self) -> Vec<&NodeId> {
        self.nodes.keys().collect()
    }
}

impl Default for InfraGraph {
    fn default() -> Self {
        Self::new()
    }
}
