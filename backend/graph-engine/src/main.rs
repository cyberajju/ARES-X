/// ARES-X Graph Engine
///
/// High-performance in-memory graph engine for infrastructure topology analysis.
/// Provides gRPC service for querying nodes, edges, finding paths, computing
/// blast radius, and identifying critical infrastructure nodes.

use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn};

mod config;
mod error;
mod graph;
mod seed;
mod server;

use config::Config;
use graph::store::InfraGraph;
use server::grpc::GraphServiceImpl;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load configuration from environment
    let config = Config::from_env();

    // Initialize tracing/logging
    init_tracing(&config.log_level);

    info!(
        listen_addr = %config.listen_addr,
        max_nodes = config.max_nodes,
        max_edges = config.max_edges,
        "Starting ARES-X Graph Engine"
    );

    // Create and seed the graph store
    let graph = seed::seed_demo_graph();
    info!(
        nodes = graph.node_count(),
        edges = graph.edge_count(),
        "Graph seeded with demo infrastructure data"
    );

    let graph_store = Arc::new(RwLock::new(graph));

    // Create gRPC service
    let service = GraphServiceImpl::new(graph_store.clone());

    info!(addr = %config.listen_addr, "gRPC server listening");

    // Parse listen address
    let addr = config.listen_addr.parse()?;

    // Start gRPC server with graceful shutdown
    // NOTE: In production, tonic-build generates a GraphServiceServer wrapper
    // from the proto file. The service would be wrapped:
    //   .add_service(GraphServiceServer::new(service))
    let server = tonic::transport::Server::builder()
        .add_service(service)
        .serve_with_shutdown(addr, shutdown_signal());

    // Run the server
    if let Err(e) = server.await {
        warn!(error = %e, "Server error");
        return Err(e.into());
    }

    info!("Graph engine shut down gracefully");
    Ok(())
}

/// Initialize the tracing subscriber for structured logging.
fn init_tracing(level: &str) {
    let filter = match level {
        "trace" => tracing::Level::TRACE,
        "debug" => tracing::Level::DEBUG,
        "warn" => tracing::Level::WARN,
        "error" => tracing::Level::ERROR,
        _ => tracing::Level::INFO,
    };

    tracing_subscriber::fmt()
        .json()
        .with_max_level(filter)
        .with_target(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .init();
}

/// Wait for a shutdown signal (SIGTERM or Ctrl+C).
async fn shutdown_signal() {
    tokio::signal::ctrl_c()
        .await
        .expect("Failed to listen for ctrl+c");
    info!("Shutdown signal received");
}
