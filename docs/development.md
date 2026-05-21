# ARES-X Development Guide

## Prerequisites

Ensure the following tools are installed on your development machine:

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | >= 20.x | Frontend development |
| Go | >= 1.21 | API Gateway, Asset Service |
| Rust | >= 1.75 | Graph Engine |
| Python | >= 3.11 | Attack Path Engine |
| Docker | >= 24.x | Container runtime |
| Docker Compose | >= 2.20 | Local orchestration |
| protoc | >= 25.x | Protocol Buffer compiler |
| pnpm | >= 8.x | Node.js package manager |

## Project Structure

```
ARES-X/
├── frontend/              # Next.js frontend
├── backend/
│   ├── api-gateway/       # Go API gateway
│   ├── graph-engine/      # Rust graph engine
│   ├── asset-service/     # Go asset service
│   └── attack-path-engine/# Python attack path engine
├── shared/
│   ├── proto/             # Protobuf definitions
│   └── types/             # Shared TypeScript types
├── deploy/
│   ├── docker/            # Dockerfiles
│   ├── docker-compose.yml # Docker Compose config
│   └── kubernetes/        # K8s manifests
└── docs/                  # Documentation
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ARES-X.git
cd ARES-X
```

### 2. Start Infrastructure (PostgreSQL + Redis)

```bash
docker compose -f deploy/docker-compose.yml up -d postgres redis
```

### 3. Run Individual Services

#### Frontend

```bash
cd frontend
pnpm install
pnpm dev
# Available at http://localhost:3000
```

#### API Gateway

```bash
cd backend/api-gateway
go mod download
go run ./cmd/server
# Available at http://localhost:8080
```

#### Graph Engine

```bash
cd backend/graph-engine
cargo build
cargo run
# Available at localhost:50051 (gRPC)
```

#### Asset Service

```bash
cd backend/asset-service
go mod download
go run ./cmd/server
# Available at http://localhost:8081
```

#### Attack Path Engine

```bash
cd backend/attack-path-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8082
# Available at http://localhost:8082
```

### 4. Run All Services Together

```bash
docker compose -f deploy/docker-compose.yml up -d
```

## Development Workflow

### Protocol Buffers

When modifying `.proto` files in `shared/proto/`:

```bash
# Generate Go code
protoc --go_out=. --go-grpc_out=. shared/proto/*.proto

# Generate Python code
python -m grpc_tools.protoc -Ishared/proto \
  --python_out=backend/attack-path-engine/app/proto \
  --grpc_python_out=backend/attack-path-engine/app/proto \
  shared/proto/*.proto
```

### Shared Types

When modifying TypeScript types in `shared/types/`:

```bash
cd shared/types
pnpm typecheck  # Verify types compile
pnpm build      # Build declaration files
```

### Environment Variables

Copy the example environment file and customize:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| APP_ENV | development | Application environment |
| POSTGRES_DSN | postgres://ares:ares_secret@localhost:5432/ares_x | Database connection string |
| REDIS_ADDR | localhost:6379 | Redis address |
| JWT_SECRET | change-me | JWT signing secret |
| GRAPH_ENGINE_ADDR | localhost:50051 | Graph engine gRPC address |
| ASSET_SERVICE_ADDR | localhost:8081 | Asset service address |
| ATTACK_PATH_ENGINE_ADDR | localhost:8082 | Attack path engine address |

## Testing

### Frontend

```bash
cd frontend
pnpm test           # Run unit tests
pnpm test:e2e       # Run end-to-end tests
pnpm lint           # Run linter
```

### API Gateway

```bash
cd backend/api-gateway
go test ./...                  # Run all tests
go test -race ./...            # Run with race detector
go test -cover ./...           # Run with coverage
```

### Graph Engine

```bash
cd backend/graph-engine
cargo test                     # Run all tests
cargo test -- --nocapture      # Run with output
cargo clippy                   # Lint
```

### Asset Service

```bash
cd backend/asset-service
go test ./...
go test -race ./...
go test -cover ./...
```

### Attack Path Engine

```bash
cd backend/attack-path-engine
pytest                         # Run all tests
pytest --cov=app               # Run with coverage
ruff check .                   # Lint
mypy app/                      # Type check
```

## Code Style

### Go

- Follow standard Go conventions (gofmt, golangci-lint)
- Use structured logging (zerolog)
- Error wrapping with context

### Rust

- Follow Rust idioms (clippy clean)
- Use `thiserror` for error types
- Prefer `Result` over `panic`

### Python

- Follow PEP 8 (enforced by ruff)
- Type annotations required (enforced by mypy)
- Use async/await for I/O operations

### TypeScript

- Strict mode enabled
- ESLint + Prettier for formatting
- Prefer interfaces over type aliases for objects

## Database Migrations

Migrations are managed per service:

```bash
# API Gateway / Asset Service (using golang-migrate)
migrate -path ./migrations -database "$POSTGRES_DSN" up

# Create a new migration
migrate create -ext sql -dir ./migrations -seq <migration_name>
```

## Debugging

### View service logs

```bash
docker compose -f deploy/docker-compose.yml logs -f <service-name>
```

### Access PostgreSQL

```bash
docker compose -f deploy/docker-compose.yml exec postgres psql -U ares -d ares_x
```

### Access Redis

```bash
docker compose -f deploy/docker-compose.yml exec redis redis-cli
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass locally
4. Submit a pull request with a clear description
5. Address review feedback
6. Squash merge when approved

### Commit Message Format

Use conventional commits:

```
feat: add blast radius visualization
fix: resolve path computation timeout
docs: update API documentation
chore: upgrade Go dependencies
refactor: extract graph query builder
test: add integration tests for asset search
```
