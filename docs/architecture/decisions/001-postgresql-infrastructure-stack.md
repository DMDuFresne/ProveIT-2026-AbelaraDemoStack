# Architecture Decision Record: PostgreSQL Placement for Ignition Gateways

## ADR-001: Infrastructure Stack for Shared Database Services

**Date:** 2024-11-03
**Status:** Accepted
**Author:** ProveIT Solutions Architect

## Context

The ProveIT Edge Stack requires PostgreSQL database support for four Ignition gateways:
- ignition_core
- ignition_scada
- ignition_mes_frontend
- ignition_mes_backend

Initial consideration was to place PostgreSQL in the Core stack alongside the core Ignition gateway and Highbyte services.

## Decision

**Create a dedicated Infrastructure stack** for shared platform services including PostgreSQL for Ignition configurations and a shared TimescaleDB instance for operational time-series data.

### Architecture Structure:

```
ProveIT Edge Stack
├── Infrastructure Stack (NEW)
│   ├── PostgreSQL (Ignition Configs)
│   ├── PgBouncer (Connection Pooling)
│   └── TimescaleDB (Shared Operational Data)
├── Core Stack
│   ├── ignition_core
│   └── highbyte
├── SCADA Stack
│   └── ignition_scada
├── MES Stack
│   ├── ignition_mes_frontend
│   ├── ignition_mes_backend
│   └── TimescaleDB (MES-specific)
└── [Other Stacks...]
```

## Rationale

### Why NOT in Core Stack:

1. **ISA-95 Violation**: Core stack represents Level 2-3 operational technology. Databases are Level 4 infrastructure services.

2. **Circular Dependencies**: Placing databases in Core creates dependency cycles where Core depends on databases which may depend on Core services.

3. **Single Responsibility**: Core stack should focus on OT integration (Ignition + Highbyte), not infrastructure persistence.

4. **Scalability Constraints**: Infrastructure services need independent scaling from OT services.

### Why Infrastructure Stack:

1. **Clear Separation**: Infrastructure services are cleanly separated from operational services.

2. **Reusability**: Database services can be shared across multiple stacks without creating inappropriate dependencies.

3. **Maintenance**: Database updates, backups, and maintenance can be performed independently.

4. **Network Isolation**: Infrastructure network can be secured separately from operations network.

## Consequences

### Positive:
- Clean architectural boundaries following ISA-95 principles
- Better security through network segmentation
- Easier horizontal scaling of database services
- Simplified backup and disaster recovery strategies
- Clear service ownership and responsibility

### Negative:
- Additional stack to manage and deploy
- Slightly more complex initial setup
- Cross-stack networking configuration required
- Additional monitoring endpoints

### Neutral:
- Requires external network declaration in Docker Compose files
- Database connection strings must reference external hosts
- Additional environment configuration files

## Implementation Details

### Network Configuration:
```yaml
networks:
  infrastructure-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/24
  operations-network:
    external: true
```

### Database Isolation Model:
- One database per Ignition gateway
- One user per database with least-privilege access
- No cross-database access between gateways
- SCRAM-SHA-256 authentication
- Connection pooling via PgBouncer

### Security Model:
```sql
-- Each gateway gets isolated database and user
CREATE DATABASE ignition_[gateway];
CREATE USER ignition_[gateway]_user WITH PASSWORD '[unique_password]';
GRANT CONNECT ON DATABASE ignition_[gateway] TO ignition_[gateway]_user;
-- Full privileges within own database only
```

### Connection Architecture:
```
Ignition Gateway → PgBouncer → PostgreSQL
                ↓
         Connection Pool
         (Session Mode)
```

## Compliance with ProveIT Constraints

✅ **TimescaleDB for time-series**: Shared operational TimescaleDB in Infrastructure stack
✅ **No MSSQL except Flow**: PostgreSQL used for Ignition, MSSQL reserved for Flow Software
✅ **Highbyte as bridge**: Architecture maintains Highbyte as sole Ignition-to-MQTT bridge
✅ **No Sparkplug B**: Standard PostgreSQL protocols, no Sparkplug B implementation
✅ **Containerized**: All services in Docker containers with proper compose files
✅ **ISA-95 Compliant**: Clear separation between infrastructure (L4) and operations (L2-3)

## Migration Path

For existing deployments:

1. Deploy Infrastructure stack first
2. Run database initialization scripts
3. Update Ignition gateway configurations with new connection strings
4. Test connectivity from each gateway
5. Migrate any existing data if needed
6. Decommission any temporary database solutions

## References

- ISA-95 Enterprise-Control System Integration
- PostgreSQL 16 Documentation
- Ignition Database Connection Best Practices
- Docker Compose Networking Guide
- TimescaleDB Multi-Node Architecture