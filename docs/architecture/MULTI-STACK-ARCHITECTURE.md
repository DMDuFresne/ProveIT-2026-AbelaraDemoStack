# ProveIT 2026 Demo Stack - Multi-Stack Architecture

## Overview

This document defines the architecture for deploying multiple ProveIT stacks with proper network isolation, subdomain-based routing, and scalability for future load balancing.

---

## Domain Structure

### Pattern
```
<service>.<stack>.yourdomain.com
```

### Examples by Stack

| Stack | Service | Domain |
|-------|---------|--------|
| Core | Ignition Gateway | `ignition.core.yourdomain.com` |
| Core | Highbyte Intelligence Hub | `highbyte.core.yourdomain.com` |
| MES | Frontend Gateway | `frontend.mes.yourdomain.com` |
| MES | Backend Gateway | `backend.mes.yourdomain.com` |
| SCADA | Ignition Gateway | `ignition.scada.yourdomain.com` |
| Analytics | Grafana | `grafana.analytics.yourdomain.com` |

### Cloudflare Requirements

- **Advanced Certificate Manager** required for multi-level wildcard certificates
- Certificate pattern: `*.*.yourdomain.com`
- Alternative: Individual certificates per subdomain (more management overhead)

---

## Network Architecture

### Design Principles

1. **Per-stack isolation** - Each stack has its own Docker bridge network
2. **Shared routing network** - Nginx instances multi-home to routing network
3. **Shared operations network** - All Ignition gateways connect to core database via operations-network
4. **Failure domain separation** - Stack failure doesn't cascade to others
5. **Future-ready** - Load balancing can be added without architectural changes

### Network Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL ACCESS                                 │
│                         (Cloudflare Tunnels)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           routing-network                                    │
│                    (Shared network for nginx instances)                      │
│                                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │ core-nginx   │  │ mes-nginx    │  │ scada-nginx  │  │analytics-nginx│   │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└──────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
           │                 │                 │                 │
           ▼                 ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          operations-network                                   │
│            (Shared by all Ignition Gateways for database access)             │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    CORE STACK SERVICES                                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ ignition-gw  │  │ highbyte     │  │ postgres     │  │ pgbouncer    │ │ │
│  │  │ (core)       │  │              │  │ (SHARED DB)  │  │ (SHARED)     │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                        │
│  │ frontend-gw  │  │ backend-gw   │  │ ignition-gw  │  ◄── Multi-homed to   │
│  │ (MES)        │  │ (MES)        │  │ (SCADA)      │      operations-network│
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      for DB access     │
│         │                 │                 │                                 │
└─────────┼─────────────────┼─────────────────┼─────────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ mes-network      │ │ (same network)   │ │ scada-network    │ │ analytics-       │
│                  │ │                  │ │                  │ │ network          │
│ ┌──────────────┐ │ │                  │ │ ┌──────────────┐ │ │ ┌──────────────┐ │
│ │ mssql        │ │ │                  │ │ │ historian    │ │ │ │ grafana      │ │
│ │ (MES-only)   │ │ │                  │ │ └──────────────┘ │ │ ├──────────────┤ │
│ └──────────────┘ │ │                  │ │                  │ │ │ prometheus   │ │
│                  │ │                  │ │                  │ │ ├──────────────┤ │
│                  │ │                  │ │                  │ │ │ timescaledb  │ │
│                  │ │                  │ │                  │ │ └──────────────┘ │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

### Network Definitions

| Network | Purpose | Created By |
|---------|---------|------------|
| `routing-network` | Shared network for nginx reverse proxies and Cloudflare tunnels | Core stack |
| `operations-network` | **Shared by ALL Ignition gateways** - hosts core PostgreSQL/PgBouncer | Core stack |
| `mes-network` | MES-specific services (MSSQL for Flow Software) | MES stack |
| `scada-network` | SCADA-specific services | SCADA stack |
| `analytics-network` | Analytics services (Grafana, Prometheus, TimescaleDB) | Analytics stack |

### Shared Database Architecture

The core stack's PostgreSQL database serves ALL Ignition gateways:
- **Core Gateway** - Native access via operations-network
- **MES Frontend Gateway** - Multi-homes to operations-network for DB access
- **MES Backend Gateway** - Multi-homes to operations-network for DB access
- **SCADA Gateway** - Multi-homes to operations-network for DB access

Each gateway connects to the database via PgBouncer (connection pooler) at `pgbouncer:5432`.

### Docker Network Configuration

```yaml
# In core stack's docker-compose.yml (creates BOTH networks)
networks:
  operations-network:
    name: operations-network
    driver: bridge
  routing-network:
    name: routing-network
    driver: bridge

services:
  postgres:
    networks:
      - operations-network  # Database on shared network

  pgbouncer:
    networks:
      - operations-network  # Connection pooler on shared network

  core-ignition-gateway:
    networks:
      - operations-network  # Access to database

  nginx:
    networks:
      - operations-network  # Access to stack services
      - routing-network     # Accessible by Cloudflare tunnel

# In MES stack's docker-compose.yml
networks:
  mes-network:
    name: mes-network
    driver: bridge
  operations-network:
    external: true          # Connect to existing operations-network
  routing-network:
    external: true

services:
  mes-frontend-gateway:
    networks:
      - mes-network         # Access to MES-specific services
      - operations-network  # Access to shared PostgreSQL via pgbouncer

  mes-backend-gateway:
    networks:
      - mes-network         # Access to MES-specific services
      - operations-network  # Access to shared PostgreSQL via pgbouncer

  mssql:
    networks:
      - mes-network         # MES-only (Flow Software database)

  nginx:
    networks:
      - mes-network         # Access to MES gateways
      - routing-network     # Accessible by Cloudflare tunnel

# In SCADA stack's docker-compose.yml
networks:
  scada-network:
    name: scada-network
    driver: bridge
  operations-network:
    external: true          # Connect to existing operations-network
  routing-network:
    external: true

services:
  scada-ignition-gateway:
    networks:
      - scada-network       # Access to SCADA-specific services
      - operations-network  # Access to shared PostgreSQL via pgbouncer
```

---

## Nginx Architecture

### Design: Per-Stack Nginx Instances

Each stack has its own nginx reverse proxy that:
- Routes traffic to services within its stack
- Multi-homes to both stack network and routing network
- Handles subdomain-based virtual hosting

### Why Per-Stack Nginx?

| Benefit | Description |
|---------|-------------|
| Isolation | Stack failures don't affect other stacks |
| Scalability | Each stack can scale independently |
| Simplicity | Configuration stays within stack context |
| Load Balancing Ready | Can add upstream servers without central changes |

### Nginx Configuration Pattern

```nginx
# stacks/core/config/nginx/nginx.conf
server {
    listen 80;
    server_name ignition.core.yourdomain.com;

    location / {
        proxy_pass http://core-ignition-gateway:8088;
        # ... proxy headers
    }
}

server {
    listen 80;
    server_name highbyte.core.yourdomain.com;

    location / {
        proxy_pass http://highbyte:45245;
        # ... proxy headers
    }
}
```

### Future Load Balancing Example

```nginx
# When scaling MES frontend to multiple gateways
upstream mes-frontend {
    least_conn;
    server mes-frontend-1:8088 weight=1;
    server mes-frontend-2:8088 weight=1;
    server mes-frontend-3:8088 weight=1;
    keepalive 32;
}

server {
    listen 80;
    server_name frontend.mes.yourdomain.com;

    location / {
        proxy_pass http://mes-frontend;
        # ... proxy headers
    }
}
```

---

## Cloudflare Tunnel Architecture

### Design: Per-Stack Tunnels

Each stack has its own Cloudflare tunnel with:
- Dedicated tunnel token
- Routes to its nginx instance
- Independent lifecycle management

### Why Per-Stack Tunnels?

| Benefit | Description |
|---------|-------------|
| Isolation | Tunnel failure only affects one stack |
| Credentials | Each stack has its own tunnel token |
| Deployment | Stacks can be deployed/updated independently |
| Security | Minimal blast radius for credential exposure |

### Cloudflare Configuration

```yaml
# Per-stack cloudflared service
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: proveit-core-cloudflared
    command: tunnel --no-autoupdate run --token ${CORE_CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - routing-network
    depends_on:
      nginx:
        condition: service_healthy
```

### Tunnel Route Configuration (Cloudflare Dashboard)

| Tunnel | Hostname Pattern | Service |
|--------|------------------|---------|
| core-tunnel | `*.core.yourdomain.com` | `http://core-nginx:80` |
| mes-tunnel | `*.mes.yourdomain.com` | `http://mes-nginx:80` |
| scada-tunnel | `*.scada.yourdomain.com` | `http://scada-nginx:80` |
| analytics-tunnel | `*.analytics.yourdomain.com` | `http://analytics-nginx:80` |

---

## Directory Structure

```
ProveIT-2026-AbelaraDemoStack/
├── docs/
│   └── architecture/
│       └── MULTI-STACK-ARCHITECTURE.md  # This document
└── stacks/
    ├── core/                            # MUST BE DEPLOYED FIRST
    │   ├── docker-compose.yml           # Creates operations-network + routing-network
    │   ├── .env
    │   ├── .env.example
    │   └── config/
    │       ├── nginx/
    │       │   └── nginx.conf           # Subdomain routing
    │       ├── postgres/
    │       │   ├── init/
    │       │   └── postgresql.conf
    │       └── cloudflare/
    ├── mes/
    │   ├── docker-compose.yml
    │   ├── .env
    │   └── config/
    │       └── nginx/
    │           └── nginx.conf
    ├── scada/
    │   ├── docker-compose.yml
    │   ├── .env
    │   └── config/
    │       └── nginx/
    │           └── nginx.conf
    └── analytics/
        ├── docker-compose.yml
        ├── .env
        └── config/
            └── nginx/
                └── nginx.conf
```

---

## Deployment Order

### Phase 1: Core Stack (REQUIRED FIRST)
```bash
# Core stack creates:
# - operations-network (shared by all Ignition gateways for database access)
# - routing-network (shared by all nginx instances for Cloudflare tunnel routing)
# - PostgreSQL database (shared by all Ignition gateways)
# - PgBouncer connection pooler
cd stacks/core
docker compose up -d

# Wait for database to be healthy before deploying other stacks
docker compose exec postgres pg_isready -U postgres
```

### Phase 2: Dependent Stacks
```bash
# Deploy after core stack is healthy
# These stacks depend on operations-network, routing-network, and pgbouncer being available
cd stacks/mes && docker compose up -d
cd stacks/scada && docker compose up -d
cd stacks/analytics && docker compose up -d
```

### Deployment Dependencies

```
    core stack ◄─── Creates operations-network + routing-network + PostgreSQL
        │
        ├──────────────┬──────────────┐
        ▼              ▼              ▼
   mes stack      scada stack   analytics stack
   (requires      (requires     (may require
   pgbouncer)     pgbouncer)    timescaledb)
```

---

## Key Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Domain Pattern | `<service>.<stack>.yourdomain.com` | Clear hierarchy, supports future growth |
| Nginx Architecture | Per-stack instances | Isolation, independent scaling |
| Network Design | Per-stack + shared operations-network | Database shared across gateways, stack isolation maintained |
| Database Access | All gateways via operations-network | Single PostgreSQL instance serves all Ignition gateways |
| Cloudflare Tunnels | Per-stack tunnels | Independent lifecycle, credential isolation |
| Load Balancing | Nginx upstream (when needed) | No architectural changes required |

---

## Appendix: Complete Services Reference

| Stack | Service | Container Name | Local Port | Local URL | Nginx URL | Cloudflare URL |
|-------|---------|----------------|------------|-----------|-----------|----------------|
| Core | Ignition Gateway | proveit-core-ignition-gateway | 8089 | `http://localhost:8089` | `http://localhost:8080` | `https://ignition.core.yourdomain.com` |
| Core | Ignition Gateway (GAN) | proveit-core-ignition-gateway | 8045 | `localhost:8045` | - | - |
| Core | Highbyte Intelligence Hub | proveit-core-highbyte | 45245 | `http://localhost:45245` | `http://localhost:8080/highbyte/` | `https://highbyte.core.yourdomain.com` |
| Core | PostgreSQL | proveit-core-postgres | 5432 | `localhost:5432` | - | - |
| Core | PgBouncer | proveit-core-pgbouncer | 6432 | `localhost:6432` | - | - |
| Core | Nginx | proveit-core-nginx | 8080 | `http://localhost:8080` | - | - |
| MES | Ignition Frontend | proveit-mes-ignition-frontend-01 | 8088 | `http://localhost:8088` | `http://localhost:8083` | `https://ignition-frontend-01.mes.yourdomain.com` |
| MES | Ignition Frontend (GAN) | proveit-mes-ignition-frontend-01 | 8043 | `localhost:8043` | - | - |
| MES | Ignition Frontend (Perspective) | proveit-mes-ignition-frontend-01 | 8060 | `localhost:8060` | - | - |
| MES | Ignition Backend | proveit-mes-ignition-backend | 8090 | `http://localhost:8090` | `http://localhost:8083/backend/` | `https://ignition-backend.mes.yourdomain.com` |
| MES | Ignition Backend (GAN) | proveit-mes-ignition-backend | 8047 | `localhost:8047` | - | - |
| MES | Ignition Backend (Perspective) | proveit-mes-ignition-backend | 8062 | `localhost:8062` | - | - |
| MES | TimescaleDB | proveit-mes-timescaledb | 5433 | `localhost:5433` | - | - |
| MES | PgBouncer | proveit-mes-pgbouncer | 6433 | `localhost:6433` | - | - |
| MES | Nginx | proveit-mes-nginx | 8083 | `http://localhost:8083` | - | - |
| SCADA | Ignition Gateway | proveit-scada-ignition-gateway | 8091 | `http://localhost:8091` | `http://localhost:8084` | `https://ignition.scada.yourdomain.com` |
| SCADA | Ignition Gateway (GAN) | proveit-scada-ignition-gateway | 8046 | `localhost:8046` | - | - |
| SCADA | Ignition Gateway (Perspective) | proveit-scada-ignition-gateway | 8063 | `localhost:8063` | - | - |
| SCADA | Nginx | proveit-scada-nginx | 8084 | `http://localhost:8084` | - | - |
| Edge | Ignition Gateway | proveit-edge-ignition-gateway-01 | 8092 | `http://localhost:8092` | `http://localhost:8082` | `https://ignition-01.edge.yourdomain.com` |
| Edge | Ignition Gateway (GAN) | proveit-edge-ignition-gateway-01 | 8048 | `localhost:8048` | - | - |
| Edge | Ignition Gateway (Perspective) | proveit-edge-ignition-gateway-01 | 8064 | `localhost:8064` | - | - |
| Edge | Fuuz Gateway | proveit-edge-fuuz-gateway | 5500-5550 | `http://localhost:5500` | `http://localhost:8082/fuuz/` | `https://fuuz.edge.yourdomain.com` |
| Edge | Nginx | proveit-edge-nginx | 8082 | `http://localhost:8082` | - | - |
| Analytics | Flow Bootstrap | proveit-analytics-flow-bootstrap | 4501 | `http://localhost:4501` (API) | - | - |
| Analytics | Flow Bootstrap (HTTP) | proveit-analytics-flow-bootstrap | 80 | `http://localhost:80` | - | - |
| Analytics | Flow Bootstrap (HTTPS) | proveit-analytics-flow-bootstrap | 443 | `https://localhost:443` | - | - |
| Analytics | MSSQL | proveit-analytics-mssql | 1433 | `localhost:1433` | - | - |
| Historian | Timebase Server | proveit-historian-timebase | 4511 | `localhost:4511` | - | - |
| Historian | Timebase Explorer | proveit-historian-explorer | 4531 | `http://localhost:4531` | `http://localhost:8086` | - |
| Historian | Timebase Collector 01 | proveit-historian-collector-01 | 4521 | `localhost:4521` | - | - |
| Historian | Timebase Collector 02 | proveit-historian-collector-02 | 4522 | `localhost:4522` | - | - |
| Historian | Nginx | proveit-historian-nginx | 8086 | `http://localhost:8086` | - | - |
| Utility | Homepage | proveit-utility-homepage | 3000 | `http://localhost:3000` | `http://localhost:8081` | `https://homepage.utility.yourdomain.com` |
| Utility | CloudBeaver (DBeaver) | proveit-utility-dbeaver | 8978 | `http://localhost:8978` | `http://localhost:8081/dbeaver/` | `https://dbeaver.utility.yourdomain.com` |
| Utility | MQTT Explorer | proveit-utility-mqtt-explorer | 4000 | `http://localhost:4000` | `http://localhost:8081/mqtt/` | `https://mqtt.utility.yourdomain.com` |
| Utility | Nginx | proveit-utility-nginx | 8081 | `http://localhost:8081` | - | - |
| Monitoring | Uptime Kuma | proveit-monitoring-uptime-kuma | 3001 | `http://localhost:3001` | `http://localhost:8085` | `https://uptime.monitor.yourdomain.com` |
| Monitoring | Nginx | proveit-monitoring-nginx | 8085 | `http://localhost:8085` | - | - |

---

## Appendix: WebSocket Configuration

All nginx configurations must support WebSocket connections for:
- Ignition Perspective sessions
- Highbyte real-time monitoring

```nginx
# WebSocket upgrade map (required in http block)
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

# WebSocket proxy configuration
location /system/websocket {
    proxy_pass http://upstream;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```
