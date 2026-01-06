# Application Access & Credentials

> **⚠️ SECURITY WARNING:** This document contains default credentials. **CHANGE ALL DEFAULT PASSWORDS IMMEDIATELY** after first deployment. Default passwords are for initial setup only and should never be used in production environments.

## Table of Contents

- [Core Stack](#core-stack)
- [SCADA Stack](#scada-stack)
- [MES Stack](#mes-stack)
- [Edge Stack](#edge-stack)
- [Historian Stack](#historian-stack)
- [Monitoring Stack](#monitoring-stack)
- [Utility Stack](#utility-stack)
- [Database Credentials](#database-credentials)
- [Ignition Gateway Shared Users](#ignition-gateway-shared-users)

---

## Core Stack

### Ignition Gateway

- **Cloudflare Tunnel URL:** `https://ignition.core.abelara.cloud`
- **Local Access URL:** `http://localhost:8080/ignition/`
- **Admin Username:** `admin` (default)
- **Admin Password:** Set via `CORE_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Environment Variables:**
  - `CORE_GATEWAY_ADMIN_USERNAME` (default: `admin`)
  - `CORE_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Shared Users (from Shared Gateway Database):**
  - `Abelara` - Password: `[tbd]`
  - `Tupinix` - Password: `[tbd]`
- **Notes:** 
  - Gateway admin credentials are set during first startup
  - Change password immediately after first login
  - Uses PostgreSQL database (see [Database Credentials](#database-credentials))
  - All Ignition Gateways are configured to use Shared Users sourced from the Shared Gateway Database (`ignition_shared`)

### Highbyte Intelligence Hub

- **Cloudflare Tunnel URL:** `https://highbyte.core.abelara.cloud`
- **Local Access URL:** `http://localhost:8080/highbyte/`
- **Username:** `admin` (default)
- **Password:** Set via `CORE_HIGHBYTE_ADMIN_PASSWORD` (default: `password`)
- **Environment Variables:**
  - `CORE_HIGHBYTE_ADMIN_PASSWORD` (default: `password`)
- **Notes:** 
  - Admin password is set via environment variable
  - Change password immediately after first login

### PostgreSQL (Internal)

- **Access:** Internal only (not exposed externally)
- **Host:** `core-pgbouncer:5432` (via PgBouncer) or `core-postgres:5432` (direct)
- **Port:** `5432` (PostgreSQL) or `6432` (PgBouncer)
- **Credentials:** See [Database Credentials](#database-credentials) section

---

## SCADA Stack

### Ignition Gateway

- **Cloudflare Tunnel URL:** `https://ignition.scada.abelara.cloud`
- **Local Access URL:** `http://localhost:8084/ignition/`
- **Admin Username:** `admin` (default)
- **Admin Password:** Set via `SCADA_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Environment Variables:**
  - `SCADA_GATEWAY_ADMIN_USERNAME` (default: `admin`)
  - `SCADA_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Shared Users (from Shared Gateway Database):**
  - `Abelara` - Password: `[tbd]`
  - `Tupinix` - Password: `[tbd]`
- **Notes:** 
  - Gateway admin credentials are set during first startup
  - Change password immediately after first login
  - Uses PostgreSQL database from Core stack (see [Database Credentials](#database-credentials))
  - All Ignition Gateways are configured to use Shared Users sourced from the Shared Gateway Database (`ignition_shared`)

---

## MES Stack

### Ignition Backend Gateway

- **Cloudflare Tunnel URL:** `https://ignition-backend.mes.abelara.cloud`
- **Local Access URL:** `http://localhost:8083/backend/`
- **Admin Username:** `admin` (default)
- **Admin Password:** Set via `MES_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Environment Variables:**
  - `MES_GATEWAY_ADMIN_USERNAME` (default: `admin`)
  - `MES_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Shared Users (from Shared Gateway Database):**
  - `Abelara` - Password: `[tbd]`
  - `Tupinix` - Password: `[tbd]`
- **Notes:** 
  - Gateway admin credentials are set during first startup
  - Change password immediately after first login
  - Uses TimescaleDB database (see [Database Credentials](#database-credentials))
  - All Ignition Gateways are configured to use Shared Users sourced from the Shared Gateway Database (`ignition_shared`)

### Ignition Frontend Gateway

- **Cloudflare Tunnel URL:** `https://ignition-frontend-01.mes.abelara.cloud`
- **Local Access URL:** `http://localhost:8083/frontend/`
- **Admin Username:** `admin` (default)
- **Admin Password:** Set via `MES_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Environment Variables:**
  - `MES_GATEWAY_ADMIN_USERNAME` (default: `admin`)
  - `MES_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Shared Users (from Shared Gateway Database):**
  - `Abelara` - Password: `[tbd]`
  - `Tupinix` - Password: `[tbd]`
- **Notes:** 
  - Gateway admin credentials are set during first startup
  - Change password immediately after first login
  - Uses TimescaleDB database (see [Database Credentials](#database-credentials))
  - All Ignition Gateways are configured to use Shared Users sourced from the Shared Gateway Database (`ignition_shared`)

### TimescaleDB (Internal)

- **Access:** Internal only (not exposed externally)
- **Host:** `mes-pgbouncer:6433` (via PgBouncer) or `mes-timescaledb:5433` (direct)
- **Port:** `5433` (TimescaleDB) or `6433` (PgBouncer)
- **Credentials:** See [Database Credentials](#database-credentials) section

---

## Edge Stack

### Ignition Gateway

- **Cloudflare Tunnel URL:** `https://ignition-01.edge.abelara.cloud` or `https://ignition.edge.abelara.cloud`
- **Local Access URL:** `http://localhost:8082/ignition/`
- **Admin Username:** `admin` (default)
- **Admin Password:** Set via `EDGE_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Environment Variables:**
  - `EDGE_GATEWAY_ADMIN_USERNAME` (default: `admin`)
  - `EDGE_IGNITION_GATEWAY_ADMIN_PASSWORD` (default: `password`)
- **Shared Users (from Shared Gateway Database):**
  - `Abelara` - Password: `[tbd]`
  - `Tupinix` - Password: `[tbd]`
- **Notes:** 
  - Gateway admin credentials are set during first startup
  - Change password immediately after first login
  - Uses PostgreSQL database from Core stack (see [Database Credentials](#database-credentials))
  - All Ignition Gateways are configured to use Shared Users sourced from the Shared Gateway Database (`ignition_shared`)

### Fuuz Device Gateway

- **Cloudflare Tunnel URL:** `https://fuuz.edge.abelara.cloud`
- **Local Access URL:** `http://localhost:8082/fuuz/`
- **Username:** Not applicable (first-run setup required)
- **Password:** Not applicable (first-run setup required)
- **Environment Variables:** None for authentication
- **Notes:** 
  - Authentication is configured during first-run setup
  - No default credentials provided

---

## Historian Stack

### Timebase Historian

- **Cloudflare Tunnel URL:** `https://historian.historian.abelara.cloud` (protected with Cloudflare Access)
- **Cloudflare Tunnel MCP Endpoint (dedicated subdomain):** `https://timebase.mcp.abelara.cloud` (SSE optimized, **no Access Policy** - open for programmatic access)
- **Cloudflare Tunnel MCP Endpoint (path-based):** `https://historian.historian.abelara.cloud/mcp` (SSE optimized, protected with Cloudflare Access)
- **Local Access URL:** `http://localhost:8086/historian/`
- **Local MCP Endpoint:** `http://localhost:8086/historian/mcp`
- **Direct MCP Endpoint:** `http://<server-ip>:4511/mcp` (also available)
- **Username:** Not applicable (authentication disabled at application level)
- **Password:** Not applicable (authentication disabled at application level)
- **Environment Variables:** None for authentication
- **Notes:** 
  - Application-level authentication is disabled in the configuration
  - **Cloudflare Access**: Recommended to protect `historian.historian.abelara.cloud` and `explorer.historian.abelara.cloud` with Access policies
  - **MCP Access**: `timebase.mcp.abelara.cloud` should remain **without Access Policy** to allow programmatic MCP client access
  - MCP endpoint accessible via Cloudflare Tunnel with SSE optimization (no proxy buffering)
  - Dedicated MCP subdomain (`timebase.mcp`) allows clean separation: protect UIs with Access, keep MCP open

### Timebase Explorer

- **Cloudflare Tunnel URL:** `https://explorer.historian.abelara.cloud`
- **Local Access URL:** `http://localhost:8086/explorer/`
- **Username:** Not applicable (authentication disabled)
- **Password:** Not applicable (authentication disabled)
- **Environment Variables:** None for authentication
- **Notes:** 
  - Authentication is disabled in the configuration
  - Access is unrestricted (consider enabling authentication for production)

---

## Monitoring Stack

### Uptime Kuma

- **Cloudflare Tunnel URL:** `https://uptime.monitor.abelara.cloud`
- **Local Access URL:** `http://localhost:8085/`
- **Username:** Not applicable (first-run setup required)
- **Password:** Not applicable (first-run setup required)
- **Environment Variables:** None for authentication
- **Notes:** 
  - Admin account is created during first-run setup
  - No default credentials provided
  - Access the application to complete initial setup

---

## Utility Stack

### Homepage Dashboard

- **Cloudflare Tunnel URL:** `https://homepage.utility.abelara.cloud`
- **Local Access URL:** `http://localhost:8081/homepage/`
- **Username:** Not applicable (no authentication)
- **Password:** Not applicable (no authentication)
- **Environment Variables:** None for authentication
- **Notes:** 
  - No authentication required
  - Public dashboard for service links

### DBeaver CloudBeaver

- **Cloudflare Tunnel URL:** `https://dbeaver.utility.abelara.cloud`
- **Local Access URL:** `http://localhost:8081/dbeaver/`
- **Username:** Not applicable (first-run setup required)
- **Password:** Not applicable (first-run setup required)
- **Environment Variables:** None for authentication
- **Notes:** 
  - Admin account is created during first-run setup
  - No default credentials provided
  - Access the application to complete initial setup

### MQTT Explorer

- **Cloudflare Tunnel URL:** `https://mqtt.utility.abelara.cloud`
- **Local Access URL:** `http://localhost:8081/mqtt/`
- **Username:** Not applicable (no authentication)
- **Password:** Not applicable (no authentication)
- **Environment Variables:** None for authentication
- **Notes:** 
  - No authentication required
  - Configure MQTT broker connection in the application

---

## Database Credentials

### Core Stack PostgreSQL

**PostgreSQL Superuser:**
- **Host:** `core-postgres:5432`
- **Username:** `postgres`
- **Password:** Set via `CORE_POSTGRES_PASSWORD` (default: `password`)
- **Environment Variable:** `CORE_POSTGRES_PASSWORD`

**PgBouncer Connection Pooler:**
- **Host:** `core-pgbouncer:6432`
- **Port:** `6432`
- **Note:** Use PgBouncer for connection pooling instead of direct PostgreSQL connection

**Ignition Gateway Databases:**

| Database | Username | Password ENV Variable | Default Password |
|----------|----------|----------------------|------------------|
| `ignition_core` | `ignition_core` | `CORE_POSTGRES_CORE_PASSWORD` | `password` |
| `ignition_scada` | `ignition_scada` | `CORE_POSTGRES_SCADA_PASSWORD` | `password` |
| `ignition_mes_frontend` | `ignition_mes_frontend` | `CORE_POSTGRES_MES_FRONTEND_PASSWORD` | `password` |
| `ignition_mes_backend` | `ignition_mes_backend` | `CORE_POSTGRES_MES_BACKEND_PASSWORD` | `password` |
| `ignition_edge` | `ignition_edge` | `CORE_POSTGRES_EDGE_PASSWORD` | `password` |
| `ignition_shared` | `ignition_shared` | `CORE_POSTGRES_SHARED_PASSWORD` | `password` |

**JDBC Connection Strings (for Ignition Gateway configuration):**

```
# Core Gateway
jdbc:postgresql://core-pgbouncer:5432/ignition_core
User: ignition_core
Password: (set via CORE_POSTGRES_CORE_PASSWORD)

# SCADA Gateway
jdbc:postgresql://core-pgbouncer:5432/ignition_scada
User: ignition_scada
Password: (set via CORE_POSTGRES_SCADA_PASSWORD)

# MES Frontend Gateway
jdbc:postgresql://core-pgbouncer:5432/ignition_mes_frontend
User: ignition_mes_frontend
Password: (set via CORE_POSTGRES_MES_FRONTEND_PASSWORD)

# MES Backend Gateway
jdbc:postgresql://core-pgbouncer:5432/ignition_mes_backend
User: ignition_mes_backend
Password: (set via CORE_POSTGRES_MES_BACKEND_PASSWORD)

# Edge Gateway
jdbc:postgresql://core-pgbouncer:5432/ignition_edge
User: ignition_edge
Password: (set via CORE_POSTGRES_EDGE_PASSWORD)

# Shared Database (write access)
jdbc:postgresql://core-pgbouncer:5432/ignition_shared
User: ignition_shared
Password: (set via CORE_POSTGRES_SHARED_PASSWORD)

# Shared Database (read access - use any gateway user)
jdbc:postgresql://core-pgbouncer:5432/ignition_shared
User: ignition_scada (or any gateway user)
Password: (use that gateway's password)
```

**Monitoring User:**
- **Username:** `monitoring_readonly`
- **Password:** Set via `CORE_POSTGRES_MONITORING_PASSWORD` (default: `password`)
- **Access:** Read-only access to all Ignition databases
- **Environment Variable:** `CORE_POSTGRES_MONITORING_PASSWORD`

### MES Stack TimescaleDB

**TimescaleDB Superuser:**
- **Host:** `mes-timescaledb:5433`
- **Username:** `postgres`
- **Password:** Set via `MES_POSTGRES_PASSWORD` (default: `password`)
- **Environment Variable:** `MES_POSTGRES_PASSWORD`

**PgBouncer Connection Pooler:**
- **Host:** `mes-pgbouncer:6433`
- **Port:** `6433`
- **Note:** Use PgBouncer for connection pooling instead of direct TimescaleDB connection

**JDBC Connection String (for Ignition Gateway configuration):**

```
jdbc:postgresql://mes-pgbouncer:6433/postgres
User: postgres
Password: (set via MES_POSTGRES_PASSWORD)
```

---

## Ignition Gateway Shared Users

All Ignition Gateways in the ProveIT 2026 Demo Stack are configured to use **Shared Users** sourced from the **Shared Gateway Database** (`ignition_shared`). This allows users to authenticate to any Ignition Gateway using the same credentials, providing a unified authentication experience across all gateways.

### Current Shared Users

| Username | Password | Notes |
|----------|----------|-------|
| `Abelara` | `[tbd]` | Shared user account |
| `Tupinix` | `[tbd]` | Shared user account |

### Gateways Using Shared Users

The following Ignition Gateways are configured to use Shared Users:

- **Core Stack** - Ignition Gateway (`ignition.core.abelara.cloud`)
- **SCADA Stack** - Ignition Gateway (`ignition.scada.abelara.cloud`)
- **MES Stack** - Ignition Backend Gateway (`ignition-backend.mes.abelara.cloud`)
- **MES Stack** - Ignition Frontend Gateway (`ignition-frontend-01.mes.abelara.cloud`)
- **Edge Stack** - Ignition Gateway (`ignition-01.edge.abelara.cloud`)

### How It Works

1. **Shared Database:** User accounts are stored in the `ignition_shared` PostgreSQL database
2. **Gateway Configuration:** Each Ignition Gateway is configured to authenticate users against the Shared Gateway Database
3. **Single Sign-On Effect:** Users can log in to any gateway using the same credentials
4. **Centralized Management:** User accounts are managed centrally in the Shared Gateway Database

### Managing Shared Users

Shared users are managed through the Ignition Gateway web interface:

1. Log in to any Ignition Gateway using admin credentials
2. Navigate to **Config** → **Users**
3. Shared users are stored in the Shared Gateway Database
4. Changes to shared users apply across all configured gateways

**Note:** Passwords for shared users are currently marked as `[tbd]` (to be determined). Set these passwords through the Ignition Gateway web interface after deployment.

---

## Security Notes

### Default Passwords

**⚠️ CRITICAL:** All default passwords listed in this document are for initial setup only. You **MUST** change these passwords immediately after deployment:

1. **Ignition Gateway Admin Passwords:**
   - Change via Ignition Gateway web interface after first login
   - Or update environment variables and restart services

2. **Database Passwords:**
   - Connect to PostgreSQL/TimescaleDB and run `ALTER USER` commands
   - Update environment variables accordingly

3. **Highbyte Admin Password:**
   - Change via Highbyte web interface after first login
   - Or update `CORE_HIGHBYTE_ADMIN_PASSWORD` environment variable

### First-Run Setup Services

The following services require first-run setup (no default credentials):

- **DBeaver CloudBeaver:** Create admin account during first access
- **Uptime Kuma:** Create admin account during first access
- **Fuuz Device Gateway:** Configure authentication during first access

### Services Without Authentication

The following services have authentication disabled or not configured:

- **Timebase Historian:** Authentication disabled in configuration
- **Timebase Explorer:** Authentication disabled in configuration
- **Homepage Dashboard:** No authentication (public dashboard)
- **MQTT Explorer:** No authentication (configure broker connection)

**Recommendation:** Enable authentication for all services before production deployment.

### Environment Variable Files

All credentials are configured via environment variables in `.env` files:

- `stacks/core/.env` - Core stack credentials
- `stacks/scada/.env` - SCADA stack credentials
- `stacks/mes/.env` - MES stack credentials
- `stacks/edge/.env` - Edge stack credentials
- `stacks/historian/.env` - Historian stack credentials
- `stacks/monitoring/.env` - Monitoring stack credentials
- `stacks/utility/.env` - Utility stack credentials

**Note:** Copy `.env.example` to `.env` and update values before deployment. Never commit `.env` files to version control.

---

## Access Methods

### Cloudflare Tunnel (External Access)

All applications are accessible via Cloudflare Tunnel using HTTPS. The tunnel provides:

- Secure external access without opening firewall ports
- TLS/SSL termination at Cloudflare edge
- DDoS protection and caching
- Zero Trust access policies (can be configured)

**Setup:** See individual stack Cloudflare README files in `stacks/{stack}/config/cloudflare/README.md`

### Local Access (Development)

All applications are accessible locally via Nginx reverse proxy:

- **Core:** `http://localhost:8080/`
- **SCADA:** `http://localhost:8084/`
- **MES:** `http://localhost:8083/`
- **Edge:** `http://localhost:8082/`
- **Historian:** `http://localhost:8086/`
- **Monitoring:** `http://localhost:8085/`
- **Utility:** `http://localhost:8081/`

**Note:** Local access is only available when running Docker Compose stacks locally. Use path-based routing (e.g., `/ignition/`, `/highbyte/`) to access specific services.

---

## Troubleshooting

### Cannot Access Application

1. **Verify service is running:**
   ```bash
   cd stacks/{stack-name}
   docker-compose ps
   ```

2. **Check service logs:**
   ```bash
   docker-compose logs {service-name}
   ```

3. **Verify Cloudflare Tunnel is connected:**
   ```bash
   docker logs proveit-{stack}-cloudflared
   ```

4. **Test local access:**
   ```bash
   curl http://localhost:{port}/{service-path}/
   ```

### Authentication Issues

1. **Default credentials not working:**
   - Verify environment variables are set correctly in `.env` file
   - Check service logs for authentication errors
   - Ensure service has completed initialization

2. **First-run setup not appearing:**
   - Clear browser cache and cookies
   - Check service logs for initialization errors
   - Verify service has completed startup

### Database Connection Issues

1. **Verify database is running:**
   ```bash
   docker-compose ps {database-service}
   ```

2. **Test database connection:**
   ```bash
   docker exec -it {database-container} psql -U {username} -d {database}
   ```

3. **Check JDBC connection string:**
   - Verify hostname matches Docker service name
   - Use PgBouncer hostname for connection pooling
   - Verify port numbers are correct

---

## Additional Resources

- [Architecture Documentation](architecture/README.md)
- [Cloudflare Tunnel Configuration](stacks/core/config/cloudflare/README.md)
- [PostgreSQL Configuration](stacks/core/config/postgres/README.md)
- [Stack README](stacks/README.md)

