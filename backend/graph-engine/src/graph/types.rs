/// Core graph type definitions.
///
/// Defines the fundamental types for representing infrastructure topology:
/// nodes (assets), edges (relationships), and their associated metadata.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;

/// Unique identifier for a node in the graph.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct NodeId(pub String);

impl NodeId {
    /// Create a new NodeId from a string.
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    /// Get the inner string reference.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for NodeId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl From<&str> for NodeId {
    fn from(s: &str) -> Self {
        Self(s.to_string())
    }
}

impl From<String> for NodeId {
    fn from(s: String) -> Self {
        Self(s)
    }
}

/// Unique identifier for an edge in the graph.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EdgeId(pub String);

impl EdgeId {
    /// Create a new EdgeId from a string.
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    /// Get the inner string reference.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for EdgeId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl From<&str> for EdgeId {
    fn from(s: &str) -> Self {
        Self(s.to_string())
    }
}

impl From<String> for EdgeId {
    fn from(s: String) -> Self {
        Self(s)
    }
}

/// The type of a node representing an infrastructure component.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum NodeType {
    Server,
    Workstation,
    Router,
    Switch,
    Firewall,
    LoadBalancer,
    Database,
    Application,
    CloudVM,
    Container,
    Identity,
    OTController,
    OTSensor,
    Unknown,
}

impl fmt::Display for NodeType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Server => write!(f, "Server"),
            Self::Workstation => write!(f, "Workstation"),
            Self::Router => write!(f, "Router"),
            Self::Switch => write!(f, "Switch"),
            Self::Firewall => write!(f, "Firewall"),
            Self::LoadBalancer => write!(f, "LoadBalancer"),
            Self::Database => write!(f, "Database"),
            Self::Application => write!(f, "Application"),
            Self::CloudVM => write!(f, "CloudVM"),
            Self::Container => write!(f, "Container"),
            Self::Identity => write!(f, "Identity"),
            Self::OTController => write!(f, "OTController"),
            Self::OTSensor => write!(f, "OTSensor"),
            Self::Unknown => write!(f, "Unknown"),
        }
    }
}

/// The type of relationship between two nodes.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EdgeType {
    ConnectsTo,
    DependsOn,
    AuthenticatesTo,
    Contains,
    AccessibleFrom,
    RoutesTo,
    ReplicatesTo,
    BacksUp,
    Monitors,
    Controls,
}

impl fmt::Display for EdgeType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ConnectsTo => write!(f, "ConnectsTo"),
            Self::DependsOn => write!(f, "DependsOn"),
            Self::AuthenticatesTo => write!(f, "AuthenticatesTo"),
            Self::Contains => write!(f, "Contains"),
            Self::AccessibleFrom => write!(f, "AccessibleFrom"),
            Self::RoutesTo => write!(f, "RoutesTo"),
            Self::ReplicatesTo => write!(f, "ReplicatesTo"),
            Self::BacksUp => write!(f, "BacksUp"),
            Self::Monitors => write!(f, "Monitors"),
            Self::Controls => write!(f, "Controls"),
        }
    }
}

/// A node in the infrastructure graph representing an asset or entity.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Node {
    /// Unique identifier for this node.
    pub id: NodeId,
    /// The type of infrastructure component.
    pub node_type: NodeType,
    /// Human-readable label.
    pub label: String,
    /// Optional description of the node.
    pub description: String,
    /// Criticality score from 0.0 (lowest) to 1.0 (highest).
    pub criticality: f64,
    /// Arbitrary key-value properties.
    pub properties: HashMap<String, String>,
    /// Tags for categorization and filtering.
    pub tags: Vec<String>,
}

impl Node {
    /// Create a new node with the given parameters.
    pub fn new(
        id: impl Into<NodeId>,
        node_type: NodeType,
        label: impl Into<String>,
        criticality: f64,
    ) -> Self {
        Self {
            id: id.into(),
            node_type,
            label: label.into(),
            description: String::new(),
            criticality: criticality.clamp(0.0, 1.0),
            properties: HashMap::new(),
            tags: Vec::new(),
        }
    }

    /// Set the description and return self for chaining.
    pub fn with_description(mut self, description: impl Into<String>) -> Self {
        self.description = description.into();
        self
    }

    /// Add a property and return self for chaining.
    pub fn with_property(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.properties.insert(key.into(), value.into());
        self
    }

    /// Add a tag and return self for chaining.
    pub fn with_tag(mut self, tag: impl Into<String>) -> Self {
        self.tags.push(tag.into());
        self
    }
}

/// A directed edge in the infrastructure graph representing a relationship.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Edge {
    /// Unique identifier for this edge.
    pub id: EdgeId,
    /// Source node ID.
    pub source: NodeId,
    /// Target node ID.
    pub target: NodeId,
    /// The type of relationship.
    pub edge_type: EdgeType,
    /// Weight/cost of traversing this edge (0.0 to 1.0, higher = easier to traverse).
    pub weight: f64,
    /// Arbitrary key-value properties.
    pub properties: HashMap<String, String>,
    /// Whether this edge can be traversed in both directions.
    pub bidirectional: bool,
}

impl Edge {
    /// Create a new edge with the given parameters.
    pub fn new(
        id: impl Into<EdgeId>,
        source: impl Into<NodeId>,
        target: impl Into<NodeId>,
        edge_type: EdgeType,
        weight: f64,
    ) -> Self {
        Self {
            id: id.into(),
            source: source.into(),
            target: target.into(),
            edge_type,
            weight: weight.clamp(0.0, 1.0),
            properties: HashMap::new(),
            bidirectional: false,
        }
    }

    /// Set bidirectional flag and return self for chaining.
    pub fn with_bidirectional(mut self, bidirectional: bool) -> Self {
        self.bidirectional = bidirectional;
        self
    }

    /// Add a property and return self for chaining.
    pub fn with_property(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.properties.insert(key.into(), value.into());
        self
    }
}
