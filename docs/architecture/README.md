# ProveIT 2026 Demo Stack - Stacks, Containers, and Ports

This document provides a comprehensive reference of all stacks, containers, and their exposed ports in the ProveIT 2026 Demo Stack.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Analytics Stack](#analytics-stack)
- [Core Stack](#core-stack)
- [Edge Stack](#edge-stack)
- [Historian Stack](#historian-stack)
- [MES Stack](#mes-stack)
- [Monitoring Stack](#monitoring-stack)
- [SCADA Stack](#scada-stack)
- [Utility Stack](#utility-stack)

---

## Quick Reference

Quick reference table for all services (excluding Nginx and Cloudflare Tunnel):

| Stack | Service | Container Name | Port(s) | Description |
|-------|---------|----------------|---------|-------------|
| **Analytics** | MSSQL Server | `proveit-analytics-mssql` | `1433` | Flow Software Backend Database |
| **Analytics** | Flow Bootstrap | `proveit-analytics-flow-bootstrap` | `4501`, `80`, `443` | Analytics Platform |
| **Core** | PostgreSQL | `proveit-core-postgres` | `5432` (localhost) | Central Database for All Ignition Gateways |
| **Core** | PgBouncer | `proveit-core-pgbouncer` | `6432` (localhost) | Connection Pooler for PostgreSQL |
| **Core** | Ignition Gateway | `proveit-core-ignition-gateway` | `8089`, `8045`, `8061` | Core Gateway - Ignition |
| **Core** | Highbyte Intelligence Hub | `proveit-core-highbyte` | `45245` | Data Transformation & Contextualization |
| **Edge** | Ignition Edge Gateway | `proveit-edge-ignition-gateway-01` | `8092`, `8048`, `8064` | Ignition Edge Gateway |
| **Edge** | Fuuz Device Gateway | `proveit-edge-fuuz-gateway` | `5500-5550` | Fuuz Device Gateway |
| **Historian** | Timebase Historian | `proveit-historian-timebase` | `4511` | Time Series Database |
| **Historian** | Timebase Explorer | `proveit-historian-explorer` | `4531` | Historian Web Interface |
| **Historian** | Timebase Collector 01 | `proveit-historian-collector-01` | `4521` | Data Collection Service |
| **Historian** | Timebase Collector 02 | `proveit-historian-collector-02` | `4522` | Data Collection Service |
| **MES** | TimescaleDB | `proveit-mes-timescaledb` | `5433` | MES Database |
| **MES** | PgBouncer | `proveit-mes-pgbouncer` | `6433` | Connection Pooler for TimescaleDB |
| **MES** | Ignition Backend | `proveit-mes-ignition-backend` | `8090`, `8047`, `8062` | MES Backend - Ignition |
| **MES** | Ignition Frontend | `proveit-mes-ignition-frontend-01` | `8088`, `8043`, `8060` | MES Frontend - Ignition |
| **Monitoring** | Uptime Kuma | `proveit-monitoring-uptime-kuma` | `3001` | Uptime Monitoring |
| **SCADA** | Ignition Gateway | `proveit-scada-ignition-gateway` | `8091`, `8046`, `8063` | SCADA Gateway - Ignition |
| **Utility** | Docker Socket Proxy | `proveit-utility-docker-socket-proxy` | - | Secure Docker API Access (internal) |
| **Utility** | Homepage | `proveit-utility-homepage` | `3000` | Web Dashboard |
| **Utility** | DBeaver | `proveit-utility-dbeaver` | `8978` | Database Management Tool |
| **Utility** | MQTT Explorer | `proveit-utility-mqtt-explorer` | `4000` | MQTT Broker Explorer |

---

## Analytics Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-analytics-mssql` | `analytics-mssql` | `1433` (default) | `1433` | MSSQL Server - Flow Software Backend Database |
| `proveit-analytics-flow-bootstrap` | `analytics-flow-bootstrap` | `4501` (default)<br>`80` (default)<br>`443` (default) | `4501`<br>`80`<br>`443` | Flow Bootstrap - Analytics Platform |

**Environment Variables:**
- `ANALYTICS_MSSQL_PORT` (default: `1433`)
- `ANALYTICS_FLOW_BOOTSTRAP_PORT` (default: `4501`)
- `ANALYTICS_FLOW_HTTP_PORT` (default: `80`)
- `ANALYTICS_FLOW_HTTPS_PORT` (default: `443`)

**Access URLs:**
- **Direct Access:** `http://localhost:4501` (Flow Bootstrap), `http://localhost:80` (Flow HTTP), `https://localhost:443` (Flow HTTPS)
- **Cloudflare URLs:** Not configured (no Nginx/Cloudflare Tunnel in this stack)

**Documentation:**
- **MSSQL Server:** [Microsoft SQL Server Documentation](https://docs.microsoft.com/en-us/sql/)
- **Flow Software:** [Flow Software Documentation](https://flow-software.com/documentation/)

**Dependencies & Relationships:**
- **analytics-mssql:** Foundation service (no dependencies)
- **analytics-flow-bootstrap:** 
  - Depends on: `analytics-mssql` (database)
  - References: `timescaledb` (from MES stack) - cross-stack dependency for time-series data
  - Network: `operations-network` (shared across stacks)

---

## Core Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-core-postgres` | `core-postgres` | `127.0.0.1:5432` (default) | `5432` | PostgreSQL Database Server - Central Database for All Ignition Gateways |
| `proveit-core-pgbouncer` | `core-pgbouncer` | `127.0.0.1:6432` (default) | `5432` | PgBouncer - Connection Pooler for PostgreSQL |
| `proveit-core-ignition-gateway` | `core-ignition-gateway` | `8089` (default)<br>`8045` (default)<br>`8061` (default) | `8088`<br>`8043`<br>`8060` | Core Gateway - Ignition |
| `proveit-core-highbyte` | `core-highbyte` | `45245` (default) | `45245` | Highbyte Intelligence Hub - Data Transformation & Contextualization |
| `proveit-core-nginx` | `core-nginx` | `8080` (default) | `80` | Nginx Reverse Proxy - Path Rewriting for Cloudflare Tunnel |
| `proveit-core-cloudflared` | `core-cloudflared` | - | - | Cloudflare Tunnel - External Access (no exposed ports) |

**Environment Variables:**
- `CORE_POSTGRES_PORT` (default: `5432`)
- `CORE_PGBOUNCER_PORT` (default: `6432`)
- `CORE_IGNITION_GATEWAY_HTTP_PORT` (default: `8089`)
- `CORE_IGNITION_GATEWAY_HTTPS_PORT` (default: `8045`)
- `CORE_IGNITION_GATEWAY_GATEWAY_PORT` (default: `8061`)
- `CORE_HIGHBYTE_WEB_PORT` (default: `45245`)
- `CORE_NGINX_PORT` (default: `8080`)

**Access URLs:**
- **Nginx (Local):** `http://localhost:8080/` → Ignition Gateway (default), `http://localhost:8080/highbyte/` → Highbyte Intelligence Hub
- **Cloudflare URLs:**
  - `https://ignition.core.yourdomain.com` → Core Ignition Gateway
  - `https://highbyte.core.yourdomain.com` → Highbyte Intelligence Hub

**Documentation:**
- **PostgreSQL:** [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- **PgBouncer:** [PgBouncer Documentation](https://www.pgbouncer.org/)
- **Ignition:** [Ignition Documentation](https://docs.inductiveautomation.com/)
- **Highbyte Intelligence Hub:** [Highbyte Documentation](https://docs.highbyte.io/)
- **Nginx:** [Nginx Documentation](https://nginx.org/en/docs/)
- **Cloudflare Tunnel:** [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

**Dependencies & Relationships:**
- **core-postgres:** Foundation service (no dependencies) - Central database for all Ignition Gateways
- **core-pgbouncer:** 
  - Depends on: `core-postgres` (healthy)
  - Purpose: Connection pooler for PostgreSQL
- **core-ignition-gateway:**
  - Depends on: `core-pgbouncer` (healthy)
  - Connects to: `core-pgbouncer` → `core-postgres` (database)
- **core-highbyte:**
  - Depends on: `core-ignition-gateway` (healthy)
  - Purpose: Data transformation and contextualization, integrates with Ignition
- **core-nginx:**
  - Depends on: `core-ignition-gateway` (healthy), `core-highbyte` (started)
  - Purpose: Reverse proxy routing traffic to Ignition and Highbyte
- **core-cloudflared:**
  - Depends on: `core-nginx` (healthy)
  - Purpose: External access tunnel routing to Nginx
- **Networks:** Creates `operations-network` and `routing-network` (shared by all stacks)

---

## Edge Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-edge-ignition-gateway-01` | `edge-ignition-gateway-01` | `8092` (default)<br>`8048` (default)<br>`8064` (default) | `8088`<br>`8043`<br>`8060` | Ignition Edge Gateway |
| `proveit-edge-fuuz-gateway` | `edge-fuuz-gateway` | `5500-5550` (default) | `5500-5550` | Fuuz Device Gateway |
| `proveit-edge-nginx` | `edge-nginx` | `8082` (default) | `80` | Nginx Reverse Proxy - Path Rewriting for Cloudflare Tunnel |
| `proveit-edge-cloudflared` | `edge-cloudflared` | - | - | Cloudflare Tunnel - External Access (no exposed ports) |

**Environment Variables:**
- `EDGE_IGNITION_GATEWAY_HTTP_PORT` (default: `8092`)
- `EDGE_IGNITION_GATEWAY_HTTPS_PORT` (default: `8048`)
- `EDGE_IGNITION_GATEWAY_GATEWAY_PORT` (default: `8064`)
- `EDGE_FUUZ_GATEWAY_PORT_RANGE` (default: `5500-5550`)
- `EDGE_NGINX_PORT` (default: `8082`)

**Access URLs:**
- **Nginx (Local):** `http://localhost:8082/` → Ignition Edge Gateway
- **Cloudflare URLs:**
  - `https://ignition-01.edge.yourdomain.com` → Ignition Edge Gateway
  - `https://ignition.edge.yourdomain.com` → Ignition Edge Gateway (alias)
  - `https://fuuz.edge.yourdomain.com` → Fuuz Device Gateway

**Documentation:**
- **Ignition Edge:** [Ignition Edge Documentation](https://docs.inductiveautomation.com/display/EDGE/Edge+Documentation)
- **Fuuz Device Gateway:** [Fuuz Documentation](https://fuuz.com/documentation/) (Contact Fuuz for specific documentation)
- **Nginx:** [Nginx Documentation](https://nginx.org/en/docs/)
- **Cloudflare Tunnel:** [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

**Dependencies & Relationships:**
- **edge-ignition-gateway-01:** Standalone service (no dependencies)
- **edge-fuuz-gateway:** Standalone service (no dependencies)
- **edge-nginx:**
  - Depends on: `edge-ignition-gateway-01` (healthy)
  - Purpose: Reverse proxy routing traffic to Ignition Edge Gateway
- **edge-cloudflared:**
  - Depends on: `edge-nginx` (healthy)
  - Purpose: External access tunnel routing to Nginx
- **Networks:** Uses `operations-network` and `routing-network` (created by Core stack)

---

## Historian Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-historian-timebase` | `historian-timebase` | `4511` (default) | `4511` | Timebase Historian - Time Series Database |
| `proveit-historian-explorer` | `historian-explorer` | `4531` (default) | `4531` | Timebase Explorer - Historian Web Interface |
| `proveit-historian-collector-01` | `historian-collector-01` | `4521` (default) | `4521` | Timebase Collector 01 - Data Collection Service |
| `proveit-historian-collector-02` | `historian-collector-02` | `4522` (default) | `4522` | Timebase Collector 02 - Data Collection Service |
| `proveit-historian-nginx` | `historian-nginx` | `8086` (default) | `80` | Nginx Reverse Proxy - Local Access |

**Environment Variables:**
- `HISTORIAN_HISTORIAN_PORT` (default: `4511`)
- `HISTORIAN_EXPLORER_PORT` (default: `4531`)
- `HISTORIAN_COLLECTOR_01_PORT` (default: `4521`)
- `HISTORIAN_COLLECTOR_02_PORT` (default: `4522`)
- `HISTORIAN_NGINX_PORT` (default: `8086`)

**Access URLs:**
- **Nginx (Local):** `http://localhost:8086/` → Timebase Explorer
- **Cloudflare URLs:** Not configured (placeholder: `explorer.historian.yourdomain.com`)

**Documentation:**
- **Timebase Historian:** [Timebase Documentation](https://timebase.flow-software.com/en/knowledge-base)
- **Nginx:** [Nginx Documentation](https://nginx.org/en/docs/)

**Dependencies & Relationships:**
- **historian-timebase:** Foundation service (no dependencies) - Time series database
- **historian-explorer:**
  - Depends on: `historian-timebase` (started)
  - Connects to: `historian-timebase` (for data visualization)
- **historian-collector-01:**
  - Depends on: `historian-timebase` (started)
  - Purpose: Data collection service writing to Timebase
- **historian-collector-02:**
  - Depends on: `historian-timebase` (started)
  - Purpose: Data collection service writing to Timebase
- **historian-nginx:**
  - Depends on: `historian-explorer` (started)
  - Purpose: Reverse proxy routing traffic to Timebase Explorer
- **Network:** Uses `timebase-network` (isolated network for Timebase services)

---

## MES Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-mes-timescaledb` | `mes-timescaledb` | `5433` (default) | `5432` | MES Database - TimescaleDB |
| `proveit-mes-pgbouncer` | `mes-pgbouncer` | `6433` (default) | `5432` | MES Connection Pooler - PgBouncer |
| `proveit-mes-ignition-backend` | `mes-ignition-backend` | `8090` (default)<br>`8047` (default)<br>`8062` (default) | `8088`<br>`8043`<br>`8060` | MES Backend - Ignition |
| `proveit-mes-ignition-frontend-01` | `mes-ignition-frontend-01` | `8088` (default)<br>`8043` (default)<br>`8060` (default) | `8088`<br>`8043`<br>`8060` | MES Frontend - Ignition |
| `proveit-mes-nginx` | `mes-nginx` | `8083` (default) | `80` | Nginx Reverse Proxy - Path Rewriting for Cloudflare Tunnel |
| `proveit-mes-cloudflared` | `mes-cloudflared` | - | - | Cloudflare Tunnel - External Access (no exposed ports) |

**Environment Variables:**
- `MES_TIMESCALE_PORT` (default: `5433`)
- `MES_PGBOUNCER_PORT` (default: `6433`)
- `MES_IGNITION_BACKEND_HTTP_PORT` (default: `8090`)
- `MES_IGNITION_BACKEND_HTTPS_PORT` (default: `8047`)
- `MES_IGNITION_BACKEND_GATEWAY_PORT` (default: `8062`)
- `MES_IGNITION_FRONTEND_HTTP_PORT` (default: `8088`)
- `MES_IGNITION_FRONTEND_HTTPS_PORT` (default: `8043`)
- `MES_IGNITION_FRONTEND_GATEWAY_PORT` (default: `8060`)
- `MES_NGINX_PORT` (default: `8083`)

**Access URLs:**
- **Nginx (Local):** `http://localhost:8083/` → MES Frontend (default), `http://localhost:8083/backend/` → MES Backend
- **Cloudflare URLs:**
  - `https://ignition-backend.mes.yourdomain.com` → MES Backend Ignition Gateway
  - `https://ignition-frontend-01.mes.yourdomain.com` → MES Frontend Ignition Gateway

**Documentation:**
- **TimescaleDB:** [TimescaleDB Documentation](https://docs.timescale.com/)
- **PgBouncer:** [PgBouncer Documentation](https://www.pgbouncer.org/)
- **Ignition:** [Ignition Documentation](https://docs.inductiveautomation.com/)
- **Nginx:** [Nginx Documentation](https://nginx.org/en/docs/)
- **Cloudflare Tunnel:** [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

**Dependencies & Relationships:**
- **mes-timescaledb:** Foundation service (no dependencies) - MES database
- **mes-pgbouncer:**
  - Depends on: `mes-timescaledb` (healthy)
  - Purpose: Connection pooler for TimescaleDB
- **mes-ignition-backend:**
  - Connects to: `mes-pgbouncer` → `mes-timescaledb` (database)
  - Purpose: Backend processing gateway
- **mes-ignition-frontend-01:**
  - Connects to: `mes-pgbouncer` → `mes-timescaledb` (database)
  - Purpose: Frontend user interface gateway
- **mes-nginx:**
  - Depends on: `mes-ignition-backend` (healthy), `mes-ignition-frontend-01` (healthy)
  - Purpose: Reverse proxy routing traffic to both Ignition gateways
- **mes-cloudflared:**
  - Depends on: `mes-nginx` (healthy)
  - Purpose: External access tunnel routing to Nginx
- **Cross-stack:** Referenced by `analytics-flow-bootstrap` (as `timescaledb`) for time-series analytics
- **Networks:** Uses `operations-network` and `routing-network` (created by Core stack)

---

## Monitoring Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-monitoring-uptime-kuma` | `monitoring-uptime-kuma` | `3001` (default) | `3001` | Uptime Kuma - Uptime Monitoring |
| `proveit-monitoring-nginx` | `monitoring-nginx` | `8085` (default) | `80` | Nginx Reverse Proxy - Path Rewriting for Cloudflare Tunnel |
| `proveit-monitoring-cloudflared` | `monitoring-cloudflared` | - | - | Cloudflare Tunnel - External Access (no exposed ports) |

**Environment Variables:**
- `MONITORING_UPTIME_KUMA_PORT` (default: `3001`)
- `MONITORING_NGINX_PORT` (default: `8085`)

**Access URLs:**
- **Nginx (Local):** `http://localhost:8085/` → Uptime Kuma
- **Cloudflare URLs:**
  - `https://uptime.monitor.yourdomain.com` → Uptime Kuma

**Documentation:**
- **Uptime Kuma:** [Uptime Kuma Documentation](https://github.com/louislam/uptime-kuma/wiki)
- **Nginx:** [Nginx Documentation](https://nginx.org/en/docs/)
- **Cloudflare Tunnel:** [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

**Dependencies & Relationships:**
- **monitoring-uptime-kuma:** Standalone service (no dependencies)
- **monitoring-nginx:**
  - Depends on: `monitoring-uptime-kuma` (healthy)
  - Purpose: Reverse proxy routing traffic to Uptime Kuma
- **monitoring-cloudflared:**
  - Depends on: `monitoring-nginx` (healthy)
  - Purpose: External access tunnel routing to Nginx
- **Networks:** Uses `operations-network` and `routing-network` (created by Core stack)

---

## SCADA Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-scada-ignition-gateway` | `scada-ignition-gateway` | `8091` (default)<br>`8046` (default)<br>`8063` (default) | `8088`<br>`8043`<br>`8060` | SCADA Gateway - Ignition |
| `proveit-scada-nginx` | `scada-nginx` | `8084` (default) | `80` | Nginx Reverse Proxy - Path Rewriting for Cloudflare Tunnel |
| `proveit-scada-cloudflared` | `scada-cloudflared` | - | - | Cloudflare Tunnel - External Access (no exposed ports) |

**Environment Variables:**
- `SCADA_IGNITION_GATEWAY_HTTP_PORT` (default: `8091`)
- `SCADA_IGNITION_GATEWAY_HTTPS_PORT` (default: `8046`)
- `SCADA_IGNITION_GATEWAY_GATEWAY_PORT` (default: `8063`)
- `SCADA_NGINX_PORT` (default: `8084`)

**Access URLs:**
- **Nginx (Local):** `http://localhost:8084/` → SCADA Ignition Gateway
- **Cloudflare URLs:**
  - `https://ignition.scada.yourdomain.com` → SCADA Ignition Gateway

**Documentation:**
- **Ignition:** [Ignition Documentation](https://docs.inductiveautomation.com/)
- **Nginx:** [Nginx Documentation](https://nginx.org/en/docs/)
- **Cloudflare Tunnel:** [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

**Dependencies & Relationships:**
- **scada-ignition-gateway:** Standalone service (no dependencies)
- **scada-nginx:**
  - Depends on: `scada-ignition-gateway` (healthy)
  - Purpose: Reverse proxy routing traffic to SCADA Ignition Gateway
- **scada-cloudflared:**
  - Depends on: `scada-nginx` (healthy)
  - Purpose: External access tunnel routing to Nginx
- **Networks:** Uses `operations-network` and `routing-network` (created by Core stack)

---

## Utility Stack

| Container Name | Service Name | Host Port(s) | Container Port(s) | Description |
|---------------|--------------|--------------|-------------------|-------------|
| `proveit-utility-docker-socket-proxy` | `utility-docker-socket-proxy` | - | - | Docker Socket Proxy - Secure Docker API Access (internal only) |
| `proveit-utility-homepage` | `utility-homepage` | `3000` (default) | `3000` | Homepage - Web Dashboard |
| `proveit-utility-dbeaver` | `utility-dbeaver` | `8978` (default) | `8978` | DBeaver - Database Management Tool |
| `proveit-utility-mqtt-explorer` | `utility-mqtt-explorer` | `4000` (default) | `4000` | MQTT Explorer - MQTT Broker Explorer |
| `proveit-utility-nginx` | `utility-nginx` | `8081` (default) | `80` | Nginx Reverse Proxy - Path Rewriting for Cloudflare Tunnel |
| `proveit-utility-cloudflared` | `utility-cloudflared` | - | - | Cloudflare Tunnel - External Access (no exposed ports) |

**Environment Variables:**
- `UTILITY_HOMEPAGE_PORT` (default: `3000`)
- `UTILITY_DBEAVER_PORT` (default: `8978`)
- `UTILITY_MQTT_EXPLORER_PORT` (default: `4000`)
- `UTILITY_NGINX_PORT` (default: `8081`)

**Access URLs:**
- **Nginx (Local):** 
  - `http://localhost:8081/` → Homepage Dashboard (default)
  - `http://localhost:8081/dbeaver/` → DBeaver CloudBeaver
  - `http://localhost:8081/mqtt/` → MQTT Explorer
- **Cloudflare URLs:**
  - `https://homepage.utility.yourdomain.com` → Homepage Dashboard
  - `https://dbeaver.utility.yourdomain.com` → DBeaver CloudBeaver
  - `https://mqtt.utility.yourdomain.com` → MQTT Explorer

**Documentation:**
- **Docker Socket Proxy:** [Docker Socket Proxy GitHub](https://github.com/Tecnativa/docker-socket-proxy)
- **Homepage:** [Homepage Documentation](https://gethomepage.dev/)
- **DBeaver CloudBeaver:** [CloudBeaver Documentation](https://dbeaver.com/docs/cloudbeaver/)
- **MQTT Explorer:** [MQTT Explorer GitHub](https://github.com/thomasnordquist/MQTT-Explorer)
- **Nginx:** [Nginx Documentation](https://nginx.org/en/docs/)
- **Cloudflare Tunnel:** [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

**Dependencies & Relationships:**
- **utility-docker-socket-proxy:** Foundation service (no dependencies) - Secure Docker API access
- **utility-homepage:**
  - Depends on: `utility-docker-socket-proxy` (healthy)
  - Connects to: `utility-docker-socket-proxy` (for Docker container monitoring)
- **utility-dbeaver:** Standalone service (no dependencies)
- **utility-mqtt-explorer:** Standalone service (no dependencies)
- **utility-nginx:**
  - Depends on: `utility-homepage` (started), `utility-dbeaver` (healthy), `utility-mqtt-explorer` (healthy)
  - Purpose: Reverse proxy routing traffic to all utility services
- **utility-cloudflared:**
  - Depends on: `utility-nginx` (healthy)
  - Purpose: External access tunnel routing to Nginx
- **Networks:** Uses `operations-network` and `routing-network` (created by Core stack)

---

## Port Summary by Stack

### Analytics Stack
- **1433** - MSSQL Server
- **80, 443, 4501** - Flow Bootstrap

### Core Stack
- **5432** - PostgreSQL (localhost only)
- **6432** - PgBouncer (localhost only)
- **8080** - Nginx
- **8089, 8045, 8061** - Ignition Gateway
- **45245** - Highbyte

### Edge Stack
- **8082** - Nginx
- **8092, 8048, 8064** - Ignition Edge Gateway
- **5500-5550** - Fuuz Gateway

### Historian Stack
- **8086** - Nginx
- **4511** - Timebase Historian
- **4531** - Timebase Explorer
- **4521** - Collector 01
- **4522** - Collector 02

### MES Stack
- **8083** - Nginx
- **5433** - TimescaleDB
- **6433** - PgBouncer
- **8090, 8047, 8062** - Ignition Backend
- **8088, 8043, 8060** - Ignition Frontend

### Monitoring Stack
- **8085** - Nginx
- **3001** - Uptime Kuma

### SCADA Stack
- **8084** - Nginx
- **8091, 8046, 8063** - Ignition Gateway

### Utility Stack
- **8081** - Nginx
- **3000** - Homepage
- **8978** - DBeaver
- **4000** - MQTT Explorer

---

## URL Summary

### Nginx Local Access URLs
- **Core:** `http://localhost:8080/` (Ignition), `http://localhost:8080/highbyte/` (Highbyte)
- **Edge:** `http://localhost:8082/` (Ignition Edge)
- **Historian:** `http://localhost:8086/` (Timebase Explorer)
- **MES:** `http://localhost:8083/` (Frontend), `http://localhost:8083/backend/` (Backend)
- **Monitoring:** `http://localhost:8085/` (Uptime Kuma)
- **SCADA:** `http://localhost:8084/` (Ignition)
- **Utility:** `http://localhost:8081/` (Homepage), `http://localhost:8081/dbeaver/` (DBeaver), `http://localhost:8081/mqtt/` (MQTT Explorer)

### Cloudflare External URLs
- **Core:**
  - `https://ignition.core.yourdomain.com` → Core Ignition Gateway
  - `https://highbyte.core.yourdomain.com` → Highbyte Intelligence Hub
- **Edge:**
  - `https://ignition-01.edge.yourdomain.com` → Ignition Edge Gateway
  - `https://ignition.edge.yourdomain.com` → Ignition Edge Gateway (alias)
  - `https://fuuz.edge.yourdomain.com` → Fuuz Device Gateway
- **Historian:** Not configured
- **MES:**
  - `https://ignition-backend.mes.yourdomain.com` → MES Backend Ignition Gateway
  - `https://ignition-frontend-01.mes.yourdomain.com` → MES Frontend Ignition Gateway
- **Monitoring:**
  - `https://uptime.monitor.yourdomain.com` → Uptime Kuma
- **SCADA:**
  - `https://ignition.scada.yourdomain.com` → SCADA Ignition Gateway
- **Utility:**
  - `https://homepage.utility.yourdomain.com` → Homepage Dashboard
  - `https://dbeaver.utility.yourdomain.com` → DBeaver CloudBeaver
  - `https://mqtt.utility.yourdomain.com` → MQTT Explorer

## Notes

- Ports marked with "default" can be overridden using the corresponding environment variables
- Ports bound to `127.0.0.1` are only accessible from the localhost
- Cloudflare Tunnel containers (`*-cloudflared`) do not expose ports directly as they route traffic through Cloudflare's network
- Port ranges (e.g., `5500-5550`) indicate multiple ports mapped as a range
- All Ignition Gateways expose three ports:
  - HTTP port (typically 8088 internally)
  - HTTPS port (typically 8043 internally)
  - Gateway port (typically 8060 internally)
- **Nginx URLs:** Local access via Nginx reverse proxy (path-based routing)
- **Cloudflare URLs:** External access via Cloudflare Tunnel (subdomain-based routing)
- All Cloudflare URLs use HTTPS (TLS terminated at Cloudflare)

---

## Architecture Overview

### Network Architecture

**Shared Networks (Created by Core Stack):**
- **`operations-network`:** Primary network for all services to communicate
- **`routing-network`:** Network for Nginx and Cloudflare Tunnel routing

**Isolated Networks:**
- **`timebase-network`:** Isolated network for Timebase Historian services (Historian stack)

### Service Dependency Chain

**Typical Stack Pattern:**
1. **Foundation Layer:** Database services (PostgreSQL, TimescaleDB, MSSQL, Timebase)
2. **Connection Pooling Layer:** PgBouncer (where applicable)
3. **Application Layer:** Ignition Gateways, Highbyte, Flow, etc.
4. **Proxy Layer:** Nginx reverse proxy
5. **External Access Layer:** Cloudflare Tunnel

### Cross-Stack Dependencies

**Analytics → MES:**
- `analytics-flow-bootstrap` references `mes-timescaledb` (as `timescaledb`) for time-series analytics data

**All Stacks → Core:**
- All stacks (except Core) use `operations-network` and `routing-network` created by Core stack
- Core stack must be started first to create shared networks

### Startup Order Recommendations

1. **Core Stack** (creates shared networks)
   - Start: `core-postgres` → `core-pgbouncer` → `core-ignition-gateway` → `core-highbyte` → `core-nginx` → `core-cloudflared`

2. **MES Stack** (referenced by Analytics)
   - Start: `mes-timescaledb` → `mes-pgbouncer` → `mes-ignition-backend/frontend` → `mes-nginx` → `mes-cloudflared`

3. **Analytics Stack** (depends on MES)
   - Start: `analytics-mssql` → `analytics-flow-bootstrap`

4. **Other Stacks** (can start in parallel after Core)
   - Edge, Historian, Monitoring, SCADA, Utility stacks can start independently

### Data Flow Patterns

**Ignition Gateway Pattern:**
- Ignition Gateway → PgBouncer → PostgreSQL/TimescaleDB
- Multiple Ignition Gateways can share the same database (Core stack pattern)

**External Access Pattern:**
- Cloudflare Tunnel → Nginx → Application Services
- All external traffic flows through this chain

**Historian Pattern:**
- Collectors → Timebase Historian → Explorer
- Isolated network for security and performance

---

*Last Updated: Generated from docker-compose.yml files*

