<p align="center">
  <img src="docs/images/proveit-logo.webp" alt="ProveIT! Conference" width="400">
</p>

<h1 align="center">ProveIT 2026 Demo Stack</h1>

<p align="center">
  <strong>A complete Industrial Edge Computing demonstration stack for the <a href="https://www.proveitconference.com/">ProveIT! Conference 2026</a></strong>
</p>

<br>

<p align="center">
  <a href="https://abelara.com">
    <img src="docs/images/abelara-logo.svg" alt="Abelara" width="200">
  </a>
</p>

<p align="center">
  <em>Built by Abelara</em>
</p>

---

## Overview

This repository contains a production-ready, containerized Industrial IoT edge stack demonstrating modern manufacturing data architecture patterns. The stack showcases integration between industry-leading platforms including Ignition SCADA, Highbyte Intelligence Hub, TimescaleDB, and Flow Software.

### Key Features

- **Multi-Stack Architecture** - Modular deployment with 8 independent stacks
- **ISA-95 Aligned** - Proper layer separation from edge to enterprise
- **Cloudflare Tunnel Integration** - Secure external access without port forwarding
- **Unified Namespace Ready** - Designed for UNS implementation with MQTT
- **Container-Native** - Full Docker Compose orchestration

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL ACCESS                                    │
│                    (Cloudflare Tunnels - *.stack.yourdomain.com)                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              routing-network                                    │
│              (Nginx reverse proxies + Cloudflare tunnel endpoints)              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            operations-network                                    │
│     (Shared: Ignition Gateways, Databases, Highbyte, Inter-service comms)        │
│                                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │    Core    │  │    MES     │  │   SCADA    │  │    Edge    │  │  Analytics │  │
│  │  Ignition  │  │  Frontend  │  │  Ignition  │  │  Ignition  │  │    Flow    │  │
│  │  Highbyte  │  │  Backend   │  │  Gateway   │  │   Fuuz     │  │   MSSQL    │  │
│  │ PostgreSQL │  │ TimescaleDB│  │            │  │            │  │            │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Stack Components

| Stack | Purpose | Key Services |
|-------|---------|--------------|
| **Core** | Central data platform | PostgreSQL, PgBouncer, Ignition Gateway, Highbyte Intelligence Hub |
| **MES** | Manufacturing Execution | TimescaleDB, MES Backend Gateway, MES Frontend Gateway |
| **SCADA** | Supervisory Control | Ignition SCADA Gateway |
| **Edge** | Edge Data Collection | Ignition Edge Gateway, Fuuz Device Gateway |
| **Historian** | Time Series Data | Timebase Historian, Explorer, Collectors |
| **Analytics** | Advanced Analytics | MSSQL, Flow Software Bootstrap |
| **Monitoring** | System Health | Uptime Kuma |
| **Utility** | Developer Tools | Homepage Dashboard, DBeaver, MQTT Explorer |

---

## Quick Start

### Prerequisites

- Docker Desktop 4.x+
- Docker Compose v2.x+
- 16GB+ RAM recommended
- Cloudflare account (for external access)

### Deployment

```bash
# Clone the repository
git clone https://github.com/your-org/ProveIT-2026-AbelaraDemoStack.git
cd ProveIT-2026-AbelaraDemoStack

# Copy environment templates
for stack in core mes scada edge historian analytics monitoring utility; do
  cp stacks/$stack/.env.example stacks/$stack/.env
done

# Edit .env files with your configuration
# IMPORTANT: Change all default passwords!

# Deploy Core stack first (creates shared networks)
cd stacks/core && docker compose up -d

# Wait for core services to be healthy
docker compose ps

# Deploy remaining stacks
cd ../mes && docker compose up -d
cd ../scada && docker compose up -d
cd ../edge && docker compose up -d
cd ../historian && docker compose up -d
cd ../analytics && docker compose up -d
cd ../monitoring && docker compose up -d
cd ../utility && docker compose up -d
```

### Deployment Order

The **Core stack must be deployed first** as it creates the shared networks and central database:

```
Phase 1: Core Stack
    │
    ├── Creates operations-network
    ├── Creates routing-network
    ├── PostgreSQL (shared database)
    └── PgBouncer (connection pooler)

Phase 2: Dependent Stacks (can be deployed in parallel)
    ├── MES
    ├── SCADA
    ├── Edge
    ├── Historian
    ├── Analytics
    ├── Monitoring
    └── Utility
```

---

## Domain Structure

External access follows the pattern: `<service>.<stack>.yourdomain.com`

| Stack | Service | URL |
|-------|---------|-----|
| Core | Ignition Gateway | `ignition.core.yourdomain.com` |
| Core | Highbyte | `highbyte.core.yourdomain.com` |
| MES | Frontend | `frontend.mes.yourdomain.com` |
| MES | Backend | `backend.mes.yourdomain.com` |
| SCADA | Gateway | `ignition.scada.yourdomain.com` |
| Edge | Gateway | `ignition.edge.yourdomain.com` |
| Historian | Explorer | `explorer.historian.yourdomain.com` |
| Monitoring | Uptime Kuma | `uptime.monitoring.yourdomain.com` |
| Utility | Homepage | `homepage.utility.yourdomain.com` |
| Utility | DBeaver | `dbeaver.utility.yourdomain.com` |

---

## Directory Structure

```
ProveIT-2026-AbelaraDemoStack/
├── README.md                    # This file
├── docs/
│   ├── architecture/
│   │   └── MULTI-STACK-ARCHITECTURE.md
│   └── images/
│       ├── proveit-logo.webp
│       └── abelara-logo.svg
└── stacks/
    ├── core/
    │   ├── docker-compose.yml
    │   ├── .env.example
    │   └── config/
    │       ├── nginx/
    │       ├── postgres/
    │       ├── cloudflare/
    │       └── highbyte/
    ├── mes/
    │   ├── docker-compose.yml
    │   ├── .env.example
    │   └── config/
    ├── scada/
    ├── edge/
    ├── historian/
    ├── analytics/
    ├── monitoring/
    └── utility/
```

---

## Technology Stack

| Category | Technology |
|----------|------------|
| **SCADA/HMI** | Inductive Automation Ignition 8.3 |
| **Data Contextualization** | Highbyte Intelligence Hub |
| **Time Series Database** | TimescaleDB, Timebase Historian |
| **Relational Database** | PostgreSQL 16, MSSQL 2022 |
| **Analytics Platform** | Flow Software |
| **Edge Gateway** | Ignition Edge, Fuuz Device Gateway |
| **Reverse Proxy** | Nginx |
| **External Access** | Cloudflare Tunnels |
| **Monitoring** | Uptime Kuma |
| **Container Runtime** | Docker / Docker Compose |

---

## Configuration

### Environment Variables

Each stack has a `.env.example` file that should be copied to `.env` and configured:

```bash
# Core stack example variables
CORE_POSTGRES_PASSWORD=<strong-password>
CORE_IGNITION_GATEWAY_ADMIN_PASSWORD=<strong-password>
CORE_HIGHBYTE_ADMIN_PASSWORD=<strong-password>
CORE_CLOUDFLARE_TUNNEL_TOKEN=<your-tunnel-token>
```

### Cloudflare Tunnel Setup

1. Create a tunnel in Cloudflare Zero Trust dashboard
2. Configure public hostname routes to point to nginx services
3. Copy tunnel token to respective `.env` files

See [Cloudflare Tunnel Documentation](stacks/core/config/cloudflare/README.md) for detailed setup instructions.

---

## Network Architecture

| Network | Purpose | Created By |
|---------|---------|------------|
| `operations-network` | Inter-service communication, database access | Core stack |
| `routing-network` | Nginx proxies, Cloudflare tunnels | Core stack |
| `timebase-network` | Historian service isolation | Historian stack |

---

## Security Considerations

> **Warning**: The default configurations use placeholder passwords. Before any deployment:

1. **Change all passwords** in `.env` files
2. **Rotate Cloudflare tunnel tokens** if exposed
3. **Enable SSL/TLS** for Ignition Gateway Network
4. **Configure PostgreSQL SSL** for production
5. **Review network isolation** requirements

See the security audit documentation for detailed hardening recommendations.

---

## Documentation

- [Multi-Stack Architecture](docs/architecture/MULTI-STACK-ARCHITECTURE.md) - Detailed architecture documentation
- [PostgreSQL Configuration](stacks/core/config/postgres/README.md) - Database setup and maintenance
- [Cloudflare Tunnel Setup](stacks/core/config/cloudflare/README.md) - External access configuration

---

## Contributing

This is a demonstration stack for the ProveIT! Conference. For questions or contributions, please contact the Abelara team.

---

## License

Copyright 2025 Abelara

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

<p align="center">
  <strong>ProveIT! Conference 2026</strong><br>
  <a href="https://www.proveitconference.com/">www.proveitconference.com</a>
</p>
