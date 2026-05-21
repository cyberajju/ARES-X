/// Graph data structures, storage, and algorithms.
///
/// This module contains the core graph engine functionality:
/// - `types`: Node, Edge, and related type definitions
/// - `store`: In-memory graph data structure with adjacency lists
/// - `algorithms`: Graph traversal and analysis algorithms
/// - `scoring`: Risk and path scoring utilities

pub mod algorithms;
pub mod scoring;
pub mod store;
pub mod types;

pub use algorithms::*;
pub use scoring::*;
pub use store::InfraGraph;
pub use types::*;
