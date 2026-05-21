# ARES-X API Documentation

## Overview

The ARES-X API is exposed through the API Gateway at `http://localhost:8080` (development) or `https://ares-x.example.com/api` (production).

All API responses follow a consistent envelope format. Authentication is required for all endpoints unless explicitly noted.

## Base URL

```
Development: http://localhost:8080/api/v1
Production:  https://ares-x.example.com/api/v1
```

## Authentication

### Login

```
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "displayName": "John Doe",
      "role": "analyst",
      "mfaEnabled": true
    },
    "session": {
      "accessToken": "eyJhbGc...",
      "refreshToken": "refresh-token-value",
      "expiresAt": "2024-01-01T01:00:00Z"
    },
    "mfaRequired": true
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### MFA Verification

```
POST /api/v1/auth/mfa/verify
```

**Request Body:**
```json
{
  "sessionId": "session-uuid",
  "code": "123456",
  "method": "totp"
}
```

### Refresh Token

```
POST /api/v1/auth/refresh
```

**Request Body:**
```json
{
  "refreshToken": "refresh-token-value"
}
```

### Logout

```
POST /api/v1/auth/logout
Authorization: Bearer <access-token>
```

## Assets

### List Assets

```
GET /api/v1/assets
Authorization: Bearer <access-token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| pageSize | integer | Items per page (default: 20, max: 100) |
| type | string | Filter by asset type |
| criticality | string | Filter by criticality level |
| status | string | Filter by status |
| search | string | Full-text search query |
| sortBy | string | Sort field (name, criticality, createdAt) |
| sortOrder | string | Sort direction (asc, desc) |

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "web-server-01",
      "hostname": "web01.internal",
      "ipAddress": "10.0.1.100",
      "type": "server",
      "criticality": "high",
      "owner": "platform-team",
      "department": "Engineering",
      "status": "active",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalCount": 150,
    "totalPages": 8,
    "hasNext": true,
    "hasPrevious": false
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Get Asset

```
GET /api/v1/assets/:id
Authorization: Bearer <access-token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "web-server-01",
    "hostname": "web01.internal",
    "ipAddress": "10.0.1.100",
    "type": "server",
    "criticality": "high",
    "owner": "platform-team",
    "department": "Engineering",
    "location": "us-east-1",
    "os": "Ubuntu",
    "osVersion": "22.04",
    "tags": { "env": "production", "tier": "frontend" },
    "metadata": {},
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
    "lastSeen": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Create Asset

```
POST /api/v1/assets
Authorization: Bearer <access-token>
Required Role: Operator, Admin
```

**Request Body:**
```json
{
  "name": "web-server-02",
  "hostname": "web02.internal",
  "ipAddress": "10.0.1.101",
  "type": "server",
  "criticality": "high",
  "owner": "platform-team",
  "department": "Engineering",
  "location": "us-east-1",
  "os": "Ubuntu",
  "osVersion": "22.04",
  "tags": { "env": "production" }
}
```

**Response (201):**
```json
{
  "success": true,
  "data": { "...asset object..." },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Update Asset

```
PUT /api/v1/assets/:id
Authorization: Bearer <access-token>
Required Role: Operator, Admin
```

**Request Body:** (partial update supported)
```json
{
  "criticality": "critical",
  "tags": { "env": "production", "monitored": "true" }
}
```

### Delete Asset

```
DELETE /api/v1/assets/:id
Authorization: Bearer <access-token>
Required Role: Admin
```

**Response (200):**
```json
{
  "success": true,
  "data": { "deleted": true },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Search Assets

```
POST /api/v1/assets/search
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "query": "web server production",
  "types": ["server", "cloud_instance"],
  "criticalities": ["high", "critical"],
  "page": 1,
  "pageSize": 20
}
```

### Bulk Import

```
POST /api/v1/assets/bulk-import
Authorization: Bearer <access-token>
Required Role: Operator, Admin
```

**Request Body:**
```json
{
  "assets": [
    { "name": "server-01", "hostname": "srv01", "...": "..." },
    { "name": "server-02", "hostname": "srv02", "...": "..." }
  ],
  "upsert": true,
  "source": "nmap-scan"
}
```

## Graph

### Query Nodes

```
POST /api/v1/graph/nodes/query
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "types": ["server", "database"],
  "filters": { "env": "production" },
  "minRiskScore": 5.0,
  "page": 1,
  "pageSize": 50
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "uuid",
        "name": "web-server-01",
        "type": "server",
        "properties": { "env": "production" },
        "riskScore": 7.5,
        "status": "active"
      }
    ],
    "totalNodes": 45
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Query Edges

```
POST /api/v1/graph/edges/query
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "types": ["network_access", "lateral_movement"],
  "sourceId": "source-uuid",
  "page": 1,
  "pageSize": 50
}
```

### Find Paths

```
POST /api/v1/graph/paths
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "sourceId": "source-node-uuid",
  "targetId": "target-node-uuid",
  "maxDepth": 10,
  "maxPaths": 5,
  "allowedEdgeTypes": ["network_access", "credential_access", "lateral_movement"]
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "paths": [
      {
        "nodes": ["..."],
        "edges": ["..."],
        "totalWeight": 4.5,
        "hopCount": 3
      }
    ],
    "totalPathsFound": 3
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Compute Blast Radius

```
POST /api/v1/graph/blast-radius
Authorization: Bearer <access-token>
Required Role: Analyst, Admin
```

**Request Body:**
```json
{
  "nodeId": "compromised-node-uuid",
  "maxDepth": 5,
  "edgeTypes": ["network_access", "lateral_movement", "privilege_escalation"]
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "originId": "compromised-node-uuid",
    "affectedNodes": ["..."],
    "totalAffected": 23,
    "aggregateRiskScore": 8.2,
    "affectedByType": {
      "server": 10,
      "database": 3,
      "workstation": 10
    }
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Get Critical Nodes

```
GET /api/v1/graph/critical-nodes
Authorization: Bearer <access-token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| topN | integer | Number of results (default: 10) |
| types | string[] | Filter by node types |
| algorithm | string | Scoring algorithm (betweenness, pagerank, degree) |

## Attack Paths

### Compute Paths

```
POST /api/v1/attack-paths/compute
Authorization: Bearer <access-token>
Required Role: Analyst, Admin
```

**Request Body:**
```json
{
  "sourceNodeId": "source-uuid",
  "targetNodeId": "target-uuid",
  "maxDepth": 15,
  "maxPaths": 10,
  "includeTactics": ["initial_access", "lateral_movement", "privilege_escalation"],
  "minLikelihood": 0.3,
  "includeMitigations": true
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "paths": [
      {
        "id": "path-uuid",
        "name": "External to Domain Admin via Web Server",
        "steps": [
          {
            "order": 1,
            "nodeId": "node-uuid",
            "nodeName": "web-server-01",
            "ttp": {
              "id": "ttp-uuid",
              "tactic": "initial_access",
              "technique": { "id": "T1190", "name": "Exploit Public-Facing Application" }
            },
            "successProbability": 0.7,
            "cumulativeRisk": 3.5
          }
        ],
        "score": {
          "overallScore": 8.5,
          "likelihoodScore": 7.0,
          "impactScore": 9.5,
          "complexityScore": 6.0,
          "riskLevel": "critical"
        }
      }
    ],
    "totalPaths": 5,
    "computationTimeMs": 2340.5
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### List Paths

```
GET /api/v1/attack-paths
Authorization: Bearer <access-token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| pageSize | integer | Items per page |
| sourceNodeId | string | Filter by source node |
| targetNodeId | string | Filter by target node |
| minScore | number | Minimum path score |
| sortBy | string | Sort field |
| sortOrder | string | Sort direction |

### Get Path Details

```
GET /api/v1/attack-paths/:id
Authorization: Bearer <access-token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| includeEvidence | boolean | Include evidence data |
| includeMitigations | boolean | Include mitigation recommendations |

### Run Simulation

```
POST /api/v1/attack-paths/simulate
Authorization: Bearer <access-token>
Required Role: Analyst, Admin
```

**Request Body:**
```json
{
  "name": "External threat scenario",
  "description": "Simulate external attacker targeting domain admin",
  "sourceNodeId": "external-entry-uuid",
  "targetNodeIds": ["dc-01-uuid", "dc-02-uuid"],
  "tactics": ["initial_access", "execution", "lateral_movement", "privilege_escalation"],
  "maxIterations": 1000,
  "timeLimitSeconds": 30,
  "assumeBreach": false,
  "parameters": {}
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "simulation-uuid",
    "discoveredPaths": ["..."],
    "totalPathsFound": 12,
    "nodesVisited": 156,
    "edgesTraversed": 423,
    "executionTimeMs": 15234,
    "findings": [
      "Critical path via unpatched web server",
      "Lateral movement possible through shared credentials"
    ],
    "recommendations": [
      "Patch CVE-2024-XXXX on web-server-01",
      "Implement network segmentation between DMZ and internal"
    ]
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

## Dashboard

### Get Stats

```
GET /api/v1/dashboard/stats
Authorization: Bearer <access-token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "totalAssets": 1250,
    "activeAssets": 1180,
    "totalAttackPaths": 89,
    "criticalPaths": 12,
    "activeAlerts": 7,
    "threatLevel": "elevated",
    "averageRiskScore": 5.4,
    "highCriticalityAssets": 45,
    "recentSimulations": 3,
    "lastUpdated": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Get Alerts

```
GET /api/v1/dashboard/alerts
Authorization: Bearer <access-token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| severity | string | Filter by severity |
| acknowledged | boolean | Filter by acknowledgment status |
| page | integer | Page number |
| pageSize | integer | Items per page |

### Get System Status

```
GET /api/v1/system/status
Authorization: Bearer <access-token>
Required Role: Admin
```

## Error Responses

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request body validation failed",
    "details": {
      "name": "Name is required",
      "ipAddress": "Invalid IP address format"
    },
    "statusCode": 400
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "req-uuid"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request validation failed |
| UNAUTHORIZED | 401 | Missing or invalid auth token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource already exists |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Downstream service unavailable |

## Rate Limiting

- Default: 100 requests per minute per user
- Simulation endpoints: 10 requests per minute per user
- Bulk operations: 5 requests per minute per user

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

## WebSocket Events

Connect to `ws://localhost:8080/ws` (or `wss://ares-x.example.com/ws` in production).

### Event Types

| Event | Description |
|-------|-------------|
| `alert.new` | New alert generated |
| `alert.resolved` | Alert resolved |
| `simulation.progress` | Simulation progress update |
| `simulation.complete` | Simulation finished |
| `asset.updated` | Asset modified |
| `path.computed` | New attack path computed |
