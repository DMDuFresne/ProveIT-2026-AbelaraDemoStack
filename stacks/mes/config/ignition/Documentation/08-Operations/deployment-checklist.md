# MES Deployment Checklist

This operational runbook provides step-by-step instructions for deploying the MES system from a clean state.

## Prerequisites

### Infrastructure
- [ ] PostgreSQL 14+ with TimescaleDB extension installed
- [ ] Ignition Gateway 8.1.30+ running
- [ ] Docker environment (if containerized deployment)
- [ ] Network connectivity between Ignition and PostgreSQL

### Access
- [ ] PostgreSQL superuser credentials (for schema creation)
- [ ] Ignition Gateway admin credentials
- [ ] SSH/RDP access to host machines

---

## Phase 1: Database Initialization

### 1.1 Schema Creation (000-015)

Execute SQL files in order:

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d proveit-mes

# Execute in order:
\i 000-db-init.sql          # Creates schemas: mes_core, mes_audit, mes_custom
\i 011-core-tables-lookup.sql   # Lookup tables (state_type, count_type, etc.)
\i 012-core-tables-master.sql   # Master tables (asset_definition, product_definition)
\i 013-core-tables-log.sql      # Log tables (state_log, production_log, etc.)
\i 015-core-hypertables.sql     # TimescaleDB hypertable configuration
```

**Verification**:
```sql
-- Check schemas exist
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('mes_core', 'mes_audit', 'mes_custom');

-- Check tables created
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'mes_core' ORDER BY table_name;
```

### 1.2 Functions & Views (031-041)

```bash
\i 031-core-functions.sql    # Helper functions
\i 041-core-views.sql        # Reporting views (vw_state_timeline, etc.)
```

**Verification**:
```sql
-- Check views exist
SELECT table_name FROM information_schema.views
WHERE table_schema = 'mes_core';

-- Check functions exist
SELECT routine_name FROM information_schema.routines
WHERE routine_schema = 'mes_core';
```

### 1.3 Seed Data (01-21)

Execute seed files in order:

```bash
# Change to seed directory
cd stacks/mes/config/database/seed

# Core lookups
\i 01-asset-types.sql
\i 02-state-types.sql
\i 03-count-types.sql
\i 04-measurement-types.sql
\i 05-downtime-reasons.sql
\i 06-product-families.sql
\i 07-product-definitions.sql
\i 08-state-definitions.sql
\i 09-kpi-definitions.sql
\i 10-asset-definitions.sql
\i 12-migrate-asset-types.sql

# Custom schema (Pilot integration)
\i 20-custom-state-xref.sql
\i 21-custom-item-xref.sql

# Verification
\i 99-verify-seed.sql
```

**Verification**:
```sql
-- Count records per table
SELECT 'asset_type' AS table_name, COUNT(*) FROM mes_core.asset_type
UNION ALL SELECT 'state_type', COUNT(*) FROM mes_core.state_type
UNION ALL SELECT 'state_definition', COUNT(*) FROM mes_core.state_definition
UNION ALL SELECT 'asset_definition', COUNT(*) FROM mes_core.asset_definition
UNION ALL SELECT 'product_definition', COUNT(*) FROM mes_core.product_definition
UNION ALL SELECT 'kpi_definition', COUNT(*) FROM mes_core.kpi_definition;
```

### 1.4 Custom Schema (999)

```bash
\i 999-custom-schema.sql    # Pilot/UNS reconciliation tables
```

**Verification**:
```sql
-- Check custom tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'mes_custom';

-- Verify state mappings
SELECT COUNT(*) FROM mes_custom.state_xref;  -- Should be 14

-- Verify item mappings
SELECT COUNT(*) FROM mes_custom.item_xref;   -- Should be 22
```

---

## Phase 2: Ignition Configuration

### 2.1 Database Connection

1. Go to **Config > Databases > Connections**
2. Create new PostgreSQL connection:

| Setting | Value |
|---------|-------|
| Name | `MES` |
| Driver | PostgreSQL |
| Connect URL | `jdbc:postgresql://localhost:5432/proveit-mes` |
| Username | `mes_user` |
| Password | `<secure password>` |
| Extra Properties | `currentSchema=mes_core` |

**Verification**:
- Click **Test Connection** - should show "Valid"
- Status should be "Valid" on Connections page

### 2.2 Tag Provider

1. Go to **Config > Tags > Realtime**
2. Create or verify tag provider:

| Setting | Value |
|---------|-------|
| Name | `MES` |
| Type | Standard |

### 2.3 Script Package Import

1. Go to **Config > Scripting > Script Modules**
2. Import script package from: `stacks/mes/config/ignition/backend/scripts/`

The `mes` package should contain:
```
mes/
├── __init__.py
├── assets.py
├── counts.py
├── db.py
├── errors.py
├── kpi.py
├── kpiCalc.py
├── lookups.py
├── notes.py
├── production.py
├── quality.py
├── resolver.py
├── state.py
└── custom/
    └── xref.py
```

**Verification**:
```python
# In Script Console
from mes import db, state, production
print("MES modules loaded successfully")

# Test DB connection
result = db.query("SELECT 1 AS test")
print("DB connection:", result)
```

### 2.4 UDT Import

1. Go to **Config > Tags > Tag Browser**
2. Right-click on `[MES]` provider
3. Select **Import Tags**
4. Import UDT definitions from: `stacks/mes/config/ignition/tags/udts.json`

**Expected UDTs (21 total)**:

| Category | UDT Name | Count |
|----------|----------|-------|
| Object | _MES/Object/State | 1 |
| Object | _MES/Object/Production | 1 |
| Object | _MES/Object/Count | 1 |
| Object | _MES/Object/Measurement | 1 |
| Object | _MES/Object/KPI | 1 |
| Object | _MES/Object/Note | 1 |
| Object | _MES/Object/StateWithReason | 1 |
| Object | _MES/Object/Product | 1 |
| Object | _MES/Object/ProcessValue | 1 |
| Equipment | _MES/Equipment/BaseEquipment | 1 |
| Equipment | _MES/Equipment/ProductionEquipment | 1 |
| Process | _MES/Process/Filler | 1 |
| Process | _MES/Process/Washer | 1 |
| Process | _MES/Process/Robot | 1 |
| Process | _MES/Process/PalletStation | 1 |
| Process | _MES/Process/CapLoader | 1 |
| Process | _MES/Process/Packager | 1 |
| Process | _MES/Process/Sealer | 1 |
| Process | _MES/Process/Tank | 1 |
| Process | _MES/Process/Vat | 1 |
| Process | _MES/Process/Labeler | 1 |
| Process | _MES/Process/Workstation | 1 |

**Verification**:
```
[MES]_MES/
├── Object/
│   ├── State
│   ├── Production
│   ├── Count
│   └── ...
├── Equipment/
│   ├── BaseEquipment
│   └── ProductionEquipment
└── Process/
    ├── Filler
    ├── Washer
    └── ...
```

### 2.5 Tag Instance Import

1. Import tag instances from: `stacks/mes/config/ignition/tags/tags.json`

**Expected Structure (45 equipment instances)**:
```
[MES]Assets/
├── Plant/
│   └── Abelara/
│       ├── Mixing/
│       │   ├── Tank1/ (Tank UDT)
│       │   ├── Tank2/ (Tank UDT)
│       │   └── Vat1/ (Vat UDT)
│       ├── Filling/
│       │   ├── Line1/
│       │   │   ├── Filler1/ (Filler UDT)
│       │   │   ├── Capper1/ (CapLoader UDT)
│       │   │   └── Labeler1/ (Labeler UDT)
│       │   └── Line2/
│       │       └── ...
│       ├── Packaging/
│       │   └── ...
│       └── Palletizing/
│           └── ...
```

**Verification**:
```python
# Count equipment instances
from mes import assets
allAssets = assets.getAllAssets()
print("Total assets:", len(allAssets))

# Check specific equipment types
fillers = assets.getAssetsByType("Filler")
print("Fillers:", len(fillers))
```

### 2.6 Gateway Timer Scripts

1. Go to **Config > Scripting > Gateway Timer Scripts**
2. Create scripts for each equipment type:

| Script Name | CRON | Source File |
|-------------|------|-------------|
| KPI_Filler | `0 * * * *` | `kpi_script_filler.py` |
| KPI_Washer | `0 * * * *` | `kpi_script_washer.py` |
| KPI_Robot | `0 * * * *` | `kpi_script_robot.py` |
| KPI_PalletStation | `0 * * * *` | `kpi_script_palletstation.py` |
| KPI_CapLoader | `0 * * * *` | `kpi_script_caploader.py` |
| KPI_Packager | `0 * * * *` | `kpi_script_packager.py` |
| KPI_Sealer | `0 * * * *` | `kpi_script_sealer.py` |
| KPI_Tank | `0 * * * *` | `kpi_script_tank.py` |
| KPI_Vat | `0 * * * *` | `kpi_script_vat.py` |
| KPI_Labeler | `0 * * * *` | `kpi_script_labeler.py` |
| KPI_Workstation | `0 * * * *` | `kpi_script_workstation.py` |

3. Enable each script

**Verification**:
- Check Gateway logs for KPI calculation entries
- Query `mes_core.kpi_log` for recent entries

### 2.7 Named Queries (Optional)

If using Perspective screens, import named queries from project resources.

---

## Phase 3: Verification

### 3.1 Database Verification

```sql
-- All tables documented
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('mes_core', 'mes_audit', 'mes_custom')
ORDER BY table_schema, table_name;

-- All views documented
SELECT table_schema, table_name
FROM information_schema.views
WHERE table_schema IN ('mes_core', 'mes_audit', 'mes_custom');

-- All functions documented
SELECT routine_schema, routine_name
FROM information_schema.routines
WHERE routine_schema IN ('mes_core', 'mes_audit', 'mes_custom');

-- Hypertables configured
SELECT hypertable_name, chunk_time_interval
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'mes_core';
```

### 3.2 Script Verification

```python
# In Ignition Script Console

# Test module imports
from mes import db, state, production, counts, kpi, kpiCalc, assets, notes
print("All modules imported successfully")

# Test asset resolution
asset = assets.getAsset("Filler 1")
print("Asset found:", asset['asset_name'])

# Test state logging
result = state.logState("Filler 1", "Running")
print("State logged:", result['state_log_id'])

# Test KPI calculation
oee = kpiCalc.getOEE("Filler 1", hours=1)
print("OEE calculated:", oee)
```

### 3.3 End-to-End Test

1. **Log a state change**:
```python
from mes import state
state.logState("Filler 1", "Running")
```

2. **Verify in database**:
```sql
SELECT * FROM mes_core.state_log
WHERE asset_name = 'Filler 1'
ORDER BY logged_at DESC LIMIT 1;
```

3. **Check tag update**:
- Navigate to `[MES]Assets/.../Filler1/State/`
- Verify tags updated

4. **Wait for KPI calculation** (or trigger manually):
```python
from mes import kpiCalc
dashboard = kpiCalc.getKPIDashboard("Filler 1", hours=1)
print(dashboard)
```

5. **Verify KPI in database**:
```sql
SELECT * FROM mes_core.kpi_log
WHERE asset_name = 'Filler 1'
ORDER BY logged_at DESC LIMIT 5;
```

---

## Phase 4: Post-Deployment

### 4.1 Documentation

- [ ] Record deployment date and version
- [ ] Document any customizations made
- [ ] Update network diagrams
- [ ] Create support contact list

### 4.2 Monitoring

- [ ] Set up Gateway status alerts
- [ ] Configure database connection monitoring
- [ ] Create KPI calculation failure alerts

### 4.3 Backup Configuration

- [ ] Configure PostgreSQL backup schedule
- [ ] Export Ignition Gateway backup
- [ ] Document recovery procedures

---

## Rollback Procedure

If deployment fails:

### Database Rollback
```sql
-- Drop schemas (DESTRUCTIVE - all data lost!)
DROP SCHEMA IF EXISTS mes_custom CASCADE;
DROP SCHEMA IF EXISTS mes_audit CASCADE;
DROP SCHEMA IF EXISTS mes_core CASCADE;
```

### Ignition Rollback
1. Disable gateway timer scripts
2. Delete imported tags and UDTs
3. Remove script modules
4. Delete database connection

---

## Troubleshooting

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| `relation "mes_core.xxx" does not exist` | SQL files run out of order | Re-run in correct sequence |
| `MesResolutionError: Asset not found` | Asset not in database | Run seed files |
| KPIs not calculating | Gateway scripts disabled | Enable in Gateway Config |
| Tag writes failing | UDTs not imported | Import udts.json first |
| FK violation on insert | Lookup data missing | Run seed files in order |

### Log Locations

| Component | Log Location |
|-----------|--------------|
| Ignition Gateway | Gateway Status > Logs |
| PostgreSQL | `/var/log/postgresql/` |
| Gateway Scripts | Filter by logger `KPI_*` |

---

## Related Documentation

- [Architecture Overview](../01-Overview/architecture.md)
- [Quick Start Guide](../01-Overview/quick-start.md)
- [Troubleshooting Guide](./troubleshooting-guide.md)
- [Schema Reference](../05-Database/schema-reference.md)
