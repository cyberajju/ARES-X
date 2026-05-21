/// gRPC server module for the graph engine.
///
/// Provides the network interface for graph operations:
/// - `grpc`: gRPC service trait implementation
/// - `handlers`: Request validation and response building

pub mod grpc;
pub mod handlers;
