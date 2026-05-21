# ARES-X

**Advanced Reconnaissance & Exploitation Simulation Platform**

ARES-X is an enterprise-grade attack path analysis and threat simulation platform designed for security teams to visualize, analyze, and prioritize cyber threats across complex infrastructure environments.

## Architecture Overview

```
                         +-------------------+
                         |    Frontend        |
                         |   (Next.js)        |
                         |    :3000           |
                         +--------+----------+
                                  |
                                  v
                         +-------------------+
                         |   API Gateway      |
                         |      (Go)          |
                         |    :8080           |
                         +--------+----------+
                                  |
                   +--------------+--------------+
                   |              |              |
                   v              v              v
          +--------+---+  +------+------+  +----+--------+
          | Graph Engine|  |Asset Service|  |Attack Path  |
          |   (Rust)    |  |    (Go)     |  |  Engine     |
          |   :50051    |  |   :8081     |  |  (Python)   |
          +--------+---+  +------+------+  |   :8082     |
                   |              |         +----+--------+
                   |              |              |
                   +--------------+--------------+
                                  |
                   +--------------+--------------+
                   |                             |
                   v                             v
          +--------+---+                +-------+----+
          | PostgreSQL  |                |   Redis    |
          |   :5432     |                |   :6379    |
          +-------------+                +------------+
```

## Tech Stack

| Service | Technology | Purpose |
|---------|-----------|---------|
| Frontend | Next.js 14 / React / TypeScript | Dashboard, visualization, user interface |
| API Gateway | Go / Chi / gRPC-Gateway | Request routing, auth, rate limiting |
| Graph Engine | Rust / Tonic / petgraph | High-performance graph traversal & analysis |
| Asset Service | Go / GORM / PostgreSQL | Asset inventory management & CRUD |
| Attack Path Engine | Python / FastAPI / NetworkX | Attack path computation & ML-based scoring |
| Database | PostgreSQL 16 | Primary data store |
| Cache | Redis 7 | Session store, caching, pub/sub |

## Services

### Frontend (Next.js)
- Real-time threat dashboard with military/tactical dark theme
- Interactive graph visualization of attack paths
- Asset inventory management interface
- Simulation configuration and results viewer

### API Gateway (Go)
- Centralized authentication and authorization (JWT + MFA)
- Request routing to backend microservices
- Rate limiting and request validation
- WebSocket support for real-time updates

### Graph Engine (Rust)
- High-performance graph storage and traversal
- Blast radius computation
- Critical node identification
- Path finding algorithms (shortest path, all paths)

### Asset Service (Go)
- CRUD operations for infrastructure assets
- Asset categorization and criticality scoring
- Bulk import/export capabilities
- Search and filtering

### Attack Path Engine (Python)
- Attack path computation using graph algorithms
- TTP (Tactics, Techniques, and Procedures) mapping
- ML-based path scoring and prioritization
- Threat simulation engine

## Project Structure

```
ARES-X/
├── frontend/                 # Next.js frontend application
├── backend/
│   ├── api-gateway/          # Go API gateway service
│   ├── graph-engine/         # Rust graph processing engine
│   ├── asset-service/        # Go asset management service
│   └── attack-path-engine/   # Python attack path analysis
├── shared/
│   ├── proto/                # Protocol Buffer definitions
│   └── types/                # Shared TypeScript type definitions
├── deploy/
│   ├── docker/               # Dockerfiles for each service
│   ├── docker-compose.yml    # Local development orchestration
│   └── kubernetes/           # K8s deployment manifests
└── docs/                     # Architecture and API documentation
```

## Getting Started

### Prerequisites

- **Node.js** >= 20.x
- **Go** >= 1.21
- **Rust** >= 1.75
- **Python** >= 3.11
- **Docker** & Docker Compose
- **kubectl** (for Kubernetes deployment)
- **protoc** (Protocol Buffer compiler)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ARES-X.git
   cd ARES-X
   ```

2. **Start all services with Docker Compose**
   ```bash
   docker compose -f deploy/docker-compose.yml up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8080
   - API Documentation: http://localhost:8080/docs

### Local Development

For individual service development, see [docs/development.md](docs/development.md).

## Documentation

- [Architecture Overview](docs/architecture.md) - System design and communication patterns
- [API Documentation](docs/api.md) - REST API endpoints and schemas
- [Development Guide](docs/development.md) - Local setup and contributing

## License

Proprietary - All rights reserved.
