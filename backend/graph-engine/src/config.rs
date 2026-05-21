/// Configuration for the graph engine service.
///
/// All settings are loaded from environment variables with sensible defaults.

/// Service configuration loaded from environment variables.
#[derive(Debug, Clone)]
pub struct Config {
    /// Address to listen on for gRPC connections.
    pub listen_addr: String,
    /// Logging level (trace, debug, info, warn, error).
    pub log_level: String,
    /// Maximum number of nodes allowed in the graph.
    pub max_nodes: usize,
    /// Maximum number of edges allowed in the graph.
    pub max_edges: usize,
}

impl Config {
    /// Load configuration from environment variables with defaults.
    pub fn from_env() -> Self {
        Self {
            listen_addr: std::env::var("GRAPH_ENGINE_LISTEN_ADDR")
                .unwrap_or_else(|_| "[::1]:50051".to_string()),
            log_level: std::env::var("GRAPH_ENGINE_LOG_LEVEL")
                .unwrap_or_else(|_| "info".to_string()),
            max_nodes: std::env::var("GRAPH_ENGINE_MAX_NODES")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(100_000),
            max_edges: std::env::var("GRAPH_ENGINE_MAX_EDGES")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(1_000_000),
        }
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            listen_addr: "[::1]:50051".to_string(),
            log_level: "info".to_string(),
            max_nodes: 100_000,
            max_edges: 1_000_000,
        }
    }
}
