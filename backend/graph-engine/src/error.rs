/// Error types for the graph engine.
///
/// Provides a comprehensive error enum covering all graph operation failures,
/// with conversions to gRPC status codes for the service layer.
use std::fmt;

/// All possible errors produced by graph operations.
#[derive(Debug, Clone, PartialEq)]
pub enum GraphError {
    /// The specified node was not found in the graph.
    NodeNotFound(String),
    /// The specified edge was not found in the graph.
    EdgeNotFound(String),
    /// A node with this ID already exists.
    DuplicateNode(String),
    /// An edge with this ID already exists.
    DuplicateEdge(String),
    /// The graph has reached its capacity limit.
    GraphFull(String),
    /// The requested operation is invalid in the current state.
    InvalidOperation(String),
    /// No path exists between the specified nodes.
    PathNotFound { source: String, target: String },
    /// An error occurred during algorithm execution.
    AlgorithmError(String),
}

impl fmt::Display for GraphError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NodeNotFound(id) => write!(f, "node not found: {}", id),
            Self::EdgeNotFound(id) => write!(f, "edge not found: {}", id),
            Self::DuplicateNode(id) => write!(f, "duplicate node: {}", id),
            Self::DuplicateEdge(id) => write!(f, "duplicate edge: {}", id),
            Self::GraphFull(msg) => write!(f, "graph full: {}", msg),
            Self::InvalidOperation(msg) => write!(f, "invalid operation: {}", msg),
            Self::PathNotFound { source, target } => {
                write!(f, "no path from {} to {}", source, target)
            }
            Self::AlgorithmError(msg) => write!(f, "algorithm error: {}", msg),
        }
    }
}

impl std::error::Error for GraphError {}

impl GraphError {
    /// Convert this error to a gRPC status code and message.
    pub fn to_grpc_status(&self) -> (i32, String) {
        match self {
            Self::NodeNotFound(_) | Self::EdgeNotFound(_) => (5, self.to_string()), // NOT_FOUND
            Self::DuplicateNode(_) | Self::DuplicateEdge(_) => (6, self.to_string()), // ALREADY_EXISTS
            Self::GraphFull(_) => (8, self.to_string()), // RESOURCE_EXHAUSTED
            Self::InvalidOperation(_) => (3, self.to_string()), // INVALID_ARGUMENT
            Self::PathNotFound { .. } => (5, self.to_string()), // NOT_FOUND
            Self::AlgorithmError(_) => (13, self.to_string()), // INTERNAL
        }
    }
}

#[cfg(feature = "grpc")]
impl From<GraphError> for tonic::Status {
    fn from(err: GraphError) -> Self {
        match &err {
            GraphError::NodeNotFound(_) | GraphError::EdgeNotFound(_) => {
                tonic::Status::not_found(err.to_string())
            }
            GraphError::DuplicateNode(_) | GraphError::DuplicateEdge(_) => {
                tonic::Status::already_exists(err.to_string())
            }
            GraphError::GraphFull(_) => tonic::Status::resource_exhausted(err.to_string()),
            GraphError::InvalidOperation(_) => {
                tonic::Status::invalid_argument(err.to_string())
            }
            GraphError::PathNotFound { .. } => tonic::Status::not_found(err.to_string()),
            GraphError::AlgorithmError(_) => tonic::Status::internal(err.to_string()),
        }
    }
}
