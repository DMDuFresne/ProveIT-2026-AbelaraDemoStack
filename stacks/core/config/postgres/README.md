# PostgreSQL Database Configuration for ProveIT Edge Stack

## Overview

This PostgreSQL instance serves as the central database server for all Ignition gateways in the ProveIT Edge Stack. It provides isolated databases for each gateway with dedicated users and security boundaries.

## Database Architecture

### Databases and Users

| Database | User | Purpose |
|----------|------|---------|
| `ignition_core` | `ignition_core` | Core gateway data storage |
| `ignition_scada` | `ignition_scada` | SCADA gateway data storage |
| `ignition_mes_frontend` | `ignition_mes_frontend` | MES Frontend gateway data |
| `ignition_mes_backend` | `ignition_mes_backend` | MES Backend gateway data |
| `ignition_edge` | `ignition_edge` | Edge gateway data storage |
| `ignition_shared` | `ignition_shared` | Shared data (all gateways have READ access) |
| `postgres` | `postgres` | System database (superuser) |
| All databases | `monitoring_readonly` | Read-only monitoring access |

### Shared Database Access

The `ignition_shared` database provides a central location for data that needs to be accessed by all gateways:
- Common lookup tables (materials, products, units of measure)
- Master data and reference data
- Cross-gateway configuration

**Access Matrix:**
| User | Access Level |
|------|--------------|
| `ignition_shared` | OWNER (full read/write) |
| `ignition_core` | READ (SELECT only) |
| `ignition_scada` | READ (SELECT only) |
| `ignition_mes_frontend` | READ (SELECT only) |
| `ignition_mes_backend` | READ (SELECT only) |
| `ignition_edge` | READ (SELECT only) |
| `monitoring_readonly` | READ (SELECT only) |

### Connection Information

**Internal Docker Network:**
- Host: `postgres`
- Port: `5432`

**External Access (if enabled):**
- Host: `localhost` or server IP
- Port: Configured via `POSTGRES_PORT` (default: 5432)

### JDBC Connection Strings

For Ignition gateway configuration:

**⚠️ SECURITY WARNING:** The default passwords below are set during database initialization. **CHANGE THESE IMMEDIATELY** after first deployment by connecting to PostgreSQL and running `ALTER USER` commands.

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

# Shared Database (write access - use for managing shared data)
jdbc:postgresql://core-pgbouncer:5432/ignition_shared
User: ignition_shared
Password: (set via CORE_POSTGRES_SHARED_PASSWORD)

# Shared Database (read access - use from any gateway)
jdbc:postgresql://core-pgbouncer:5432/ignition_shared
User: ignition_scada  (or any gateway user)
Password: (use that gateway's password)
```

**Note:** Use `core-pgbouncer` as the host (not `core-postgres`) to benefit from connection pooling.

## Security Configuration

### Password Management

**⚠️ CRITICAL SECURITY REQUIREMENT:**

The database users are created with **default passwords** hardcoded in the initialization script. You **MUST** change these passwords immediately after deployment:

```bash
# Connect to PostgreSQL
docker exec -it proveit-core-postgres psql -U postgres

# Change passwords for each user
ALTER USER ignition_core WITH PASSWORD 'YourSecurePassword1!';
ALTER USER ignition_scada WITH PASSWORD 'YourSecurePassword2!';
ALTER USER ignition_mes_frontend WITH PASSWORD 'YourSecurePassword3!';
ALTER USER ignition_mes_backend WITH PASSWORD 'YourSecurePassword4!';
ALTER USER ignition_edge WITH PASSWORD 'YourSecurePassword5!';
ALTER USER ignition_shared WITH PASSWORD 'YourSecurePassword6!';
ALTER USER monitoring_readonly WITH PASSWORD 'YourSecurePassword7!';
\q
```

**After changing passwords:**
1. Update Ignition gateway database connection configurations
2. Restart affected gateway containers
3. Test database connectivity

**Best Practices:**
1. **Never use default passwords in production**
2. **Never commit passwords to version control**
3. Copy `.env.example` to `.env`
4. Use a password manager for production deployments

### Password Requirements

- Minimum 12 characters
- Include uppercase and lowercase letters
- Include numbers and special characters
- Unique for each database user
- Rotate regularly (every 90 days recommended)

### Network Security

- PostgreSQL runs on an isolated Docker network
- External port exposure is optional (disable for production)
- SSL/TLS can be enabled via `postgresql.conf`
- Each gateway has isolated database access

## Performance Tuning

### Resource Allocation

Default settings are configured in `postgresql.conf`. Key settings:

- **shared_buffers:** 512MB (25% of available RAM)
- **effective_cache_size:** 2GB (50-75% of available RAM)
- **work_mem:** 8MB (increase for complex queries)
- **maintenance_work_mem:** 128MB (for VACUUM, INDEX operations)
- **max_connections:** 200 (suitable for 4 gateways + pooling)

Adjust these in `config/postgres/postgresql.conf` based on your server resources.

### Connection Pool Sizing

**PgBouncer Configuration:**
- **Pool Mode:** Session (required for Ignition)
- **Max Client Connections:** 200
- **Default Pool Size:** 25 per database
- **Min Pool Size:** 5 per database

**Ignition Gateway Configuration:**
Each Ignition gateway should configure its connection pool to use PgBouncer:

- **Min Connections:** 5
- **Max Connections:** 30
- **Total connections:** 5 gateways × 30 = 150 (within 200 limit)

## Backup and Recovery

### Automated Backups

Run the backup script manually or via cron:

```bash
# Backup all databases
./scripts/postgres-backup.sh

# Backup specific database
./scripts/postgres-backup.sh -d ignition_core

# Backup with compression and 30-day retention
./scripts/postgres-backup.sh -c -r 30
```

### Scheduled Backups (Cron)

Add to crontab for automated backups:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/postgres-backup.sh -c -r 30

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 /path/to/scripts/postgres-backup.sh -t full -c -r 90
```

### Restore Process

```bash
# Restore from backup
./scripts/postgres-restore.sh -f backups/ignition_core_full_20240101_120000.sql

# Restore to different database
./scripts/postgres-restore.sh -f backup.sql -d ignition_core_test

# Force restore without confirmation
./scripts/postgres-restore.sh -f backup.sql -F
```

## Maintenance Operations

### Regular Maintenance

Run maintenance tasks to optimize performance:

```bash
# Run all maintenance tasks
./scripts/postgres-maintenance.sh

# Run specific maintenance task
./scripts/postgres-maintenance.sh -t vacuum
./scripts/postgres-maintenance.sh -t analyze
./scripts/postgres-maintenance.sh -t reindex

# Check database health
./scripts/postgres-maintenance.sh -t health

# View database statistics
./scripts/postgres-maintenance.sh -t stats
```

### Maintenance Schedule

Recommended maintenance schedule:

- **Daily:** VACUUM ANALYZE (automatic via autovacuum)
- **Weekly:** Health checks and statistics review
- **Monthly:** REINDEX for heavily used tables
- **Quarterly:** Full maintenance with manual VACUUM FULL

## Monitoring

### Health Checks

The Docker health check runs every 30 seconds:

```bash
# Check container health
docker inspect proveit-core-postgres --format='{{.State.Health.Status}}'

# View health check logs
docker inspect proveit-core-postgres --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

### Performance Metrics

Monitor these key metrics:

1. **Connection Count**
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

2. **Database Size**
   ```sql
   SELECT pg_database_size('ignition_core');
   ```

3. **Cache Hit Ratio** (should be >90%)
   ```sql
   SELECT sum(blks_hit)*100/sum(blks_hit+blks_read) AS cache_hit_ratio
   FROM pg_stat_database;
   ```

4. **Long Running Queries**
   ```sql
   SELECT pid, age(clock_timestamp(), query_start), usename, query
   FROM pg_stat_activity
   WHERE state != 'idle' AND query NOT ILIKE '%pg_stat_activity%'
   ORDER BY query_start;
   ```

## Troubleshooting

### Common Issues

1. **Container won't start**
   - Check logs: `docker logs proveit-postgres`
   - Verify volume permissions
   - Ensure no port conflicts

2. **Connection refused**
   - Verify container is running: `docker ps`
   - Check network connectivity
   - Verify firewall rules

3. **Authentication failed**
   - Verify password in `.env` file
   - Check user exists in database
   - Verify connection string format

4. **Performance issues**
   - Run maintenance script
   - Check for long-running queries
   - Review connection pool settings
   - Adjust memory parameters

### Debug Commands

```bash
# View PostgreSQL logs
docker logs -f proveit-core-postgres

# Connect to PostgreSQL CLI
docker exec -it proveit-core-postgres psql -U postgres

# Check running queries
docker exec proveit-core-postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Check database sizes
docker exec proveit-core-postgres psql -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;"
```

## Upgrade Process

To upgrade PostgreSQL version:

1. **Backup all databases**
   ```bash
   ./scripts/postgres-backup.sh -c
   ```

2. **Stop the container**
   ```bash
   docker-compose down
   ```

3. **Update version in `.env`**
   ```bash
   POSTGRES_VERSION=16.1-alpine
   ```

4. **Start with new version**
   ```bash
   docker-compose up -d postgres
   ```

5. **Verify functionality**
   ```bash
   ./scripts/postgres-maintenance.sh -t health
   ```

## Best Practices

1. **Always backup before maintenance**
2. **Test restore procedures regularly**
3. **Monitor disk space for data and backup volumes**
4. **Review logs weekly for errors or warnings**
5. **Keep PostgreSQL version updated for security patches**
6. **Document any custom configurations or modifications**
7. **Use prepared statements in Ignition for better performance**
8. **Configure Ignition store-and-forward for database resilience**

## Support

For issues or questions:
1. Check container logs first
2. Run health check script
3. Review this documentation
4. Consult PostgreSQL documentation: https://www.postgresql.org/docs/