# MES Troubleshooting Guide

This guide provides solutions for common issues encountered when operating the MES system.

---

## Database Errors

### Error: `relation "mes_core.xxx" does not exist`

**Cause**: SQL schema files were not executed or executed out of order.

**Solution**:
```sql
-- Check if schema exists
SELECT schema_name FROM information_schema.schemata
WHERE schema_name = 'mes_core';

-- If missing, re-run initialization
\i 000-db-init.sql
\i 011-core-tables-lookup.sql
\i 012-core-tables-master.sql
\i 013-core-tables-log.sql
```

---

### Error: `violates foreign key constraint`

**Cause**: Referenced record doesn't exist (e.g., asset_id, state_id, product_id).

**Solution**:
```sql
-- Check if asset exists
SELECT * FROM mes_core.asset_definition
WHERE asset_id = <id> OR asset_name = '<name>';

-- Check if state exists
SELECT * FROM mes_core.state_definition
WHERE state_id = <id> OR state_name = '<name>';

-- If missing, add seed data
\i seed/10-asset-definitions.sql
\i seed/08-state-definitions.sql
```

**Python check**:
```python
from mes import assets, lookups

# Verify asset exists
try:
    asset = assets.getAsset("Filler 1")
    print("Asset found:", asset)
except Exception as e:
    print("Asset not found:", e)

# Verify state exists
states = lookups.getAllStates()
print("Available states:", [s['state_name'] for s in states])
```

---

### Error: `duplicate key value violates unique constraint`

**Cause**: Attempting to insert a record that already exists.

**Solution**:
```sql
-- For lookup tables, use UPSERT pattern
INSERT INTO mes_core.state_definition (state_name, state_type_id)
VALUES ('Running', 1)
ON CONFLICT (state_name) DO UPDATE SET
    state_type_id = EXCLUDED.state_type_id,
    updated_at = CURRENT_TIMESTAMP;
```

---

### Error: `permission denied for schema mes_core`

**Cause**: Database user lacks necessary permissions.

**Solution**:
```sql
-- Grant schema access
GRANT USAGE ON SCHEMA mes_core TO mes_user;
GRANT USAGE ON SCHEMA mes_audit TO mes_user;
GRANT USAGE ON SCHEMA mes_custom TO mes_user;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mes_core TO mes_user;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA mes_audit TO mes_user;
GRANT SELECT ON ALL TABLES IN SCHEMA mes_custom TO mes_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA mes_core TO mes_user;
```

---

## Script Errors

### Error: `MesResolutionError: Asset 'X' not found`

**Cause**: The asset name, ID, or tag path doesn't match any record in `asset_definition`.

**Solution**:
```python
from mes import assets

# Check available assets
allAssets = assets.getAllAssets()
for a in allAssets:
    print(a['asset_name'], a['tag_path'])

# Try different identifier types
# By name
asset = assets.getAsset("Filler 1")

# By ID
asset = assets.getAsset(5)

# By tag path
asset = assets.getAsset("Assets/Filling/Line1/Filler1")
```

**Database check**:
```sql
-- Search for partial matches
SELECT asset_id, asset_name, tag_path
FROM mes_core.asset_definition
WHERE LOWER(asset_name) LIKE '%filler%'
   OR LOWER(tag_path) LIKE '%filler%';
```

---

### Error: `MesResolutionError: State 'X' not found`

**Cause**: State name doesn't match any record in `state_definition`.

**Solution**:
```python
from mes import lookups

# List all available states
states = lookups.getAllStates()
for s in states:
    print("State:", s['state_name'], "Type:", s['state_type_name'])
```

**Database check**:
```sql
-- Search for states
SELECT sd.state_id, sd.state_name, st.state_type_name
FROM mes_core.state_definition sd
JOIN mes_core.state_type st ON st.state_type_id = sd.state_type_id
WHERE sd.removed IS DISTINCT FROM TRUE
ORDER BY st.state_type_name, sd.state_name;
```

---

### Error: `MesValidationError: Invalid value for field 'X'`

**Cause**: Parameter validation failed (e.g., negative quantity, invalid date).

**Solution**:
```python
from mes import counts
from mes.errors import MesValidationError

try:
    # This will fail - quantity must be >= 0
    counts.recordCount("Filler 1", "Good", -5, "Cola")
except MesValidationError as e:
    print("Field:", e.field)
    print("Value:", e.value)
    print("Message:", str(e))

# Correct usage
counts.recordCount("Filler 1", "Good", 5, "Cola")
```

---

### Error: `MesConflictError: Production run already active`

**Cause**: Attempting to start a new production run when one is already active.

**Solution**:
```python
from mes import production

# Check for active production
active = production.getActiveProduction("Filler 1")
if active:
    print("Active run:", active['production_log_id'])
    print("Product:", active['product_name'])

    # End the active run first
    production.endProductionRun("Filler 1")

# Now start new run
production.startProductionRun("Filler 1", "Orange Soda 0.5L")
```

---

## Tag Issues

### Issue: LogTrigger Stuck at TRUE

**Cause**: Tag change script failed or LogTrigger not being reset.

**Symptoms**:
- KPIs not being logged to database
- LogTrigger tag stays TRUE after write

**Solution**:

1. **Check tag change script exists** on KPI UDT LogTrigger tag
2. **Verify script content**:
```python
# The script should reset LogTrigger after logging
if currentValue.value == True:
    # ... logging logic ...
    system.tag.writeBlocking([tagPath], [False])  # Reset trigger
```

3. **Manual reset**:
```python
# Find stuck triggers
paths = system.tag.browse("[MES]Assets", {"tagType": "AtomicTag"})
for tag in paths.results:
    if "LogTrigger" in tag['fullPath']:
        value = system.tag.readBlocking([tag['fullPath']])[0].value
        if value == True:
            print("Stuck trigger:", tag['fullPath'])
            # Reset manually
            system.tag.writeBlocking([tag['fullPath']], [False])
```

---

### Issue: KPIs Not Updating

**Cause**: Gateway scripts not running, or tag paths misconfigured.

**Diagnostic Steps**:

1. **Check gateway script status**:
   - Go to Gateway > Config > Scripting > Gateway Timer Scripts
   - Verify scripts are enabled
   - Check "Last Run" timestamp

2. **Check gateway logs**:
   - Filter by logger: `KPI_*`
   - Look for errors or warnings

3. **Verify asset tag_path**:
```sql
SELECT asset_name, tag_path
FROM mes_core.asset_definition
WHERE tag_path IS NULL OR tag_path = '';
```

4. **Test manual KPI calculation**:
```python
from mes import kpiCalc

# Test calculation
oee = kpiCalc.getOEE("Filler 1", hours=1)
print("OEE:", oee)

# If this works, issue is with gateway script or tag writing
```

---

### Issue: Tags Not Found at Expected Path

**Cause**: UDT instances not created or path mismatch.

**Solution**:
```python
# Verify tag exists
paths = [
    "[MES]Assets/Filling/Line1/Filler1/KPIs/OEE/Value",
    "[MES]Assets/Filling/Line1/Filler1/State/CurrentState"
]
results = system.tag.readBlocking(paths)

for path, result in zip(paths, results):
    if result.quality.isGood():
        print("OK:", path, "=", result.value)
    else:
        print("ERROR:", path, "-", result.quality)
```

**Check tag_path in database matches actual tag path**:
```sql
SELECT asset_name, tag_path
FROM mes_core.asset_definition
WHERE tag_path LIKE '%Filler1%';
```

---

## Performance Issues

### Issue: Slow Queries on Log Tables

**Cause**: Missing indexes or querying without time range filter.

**Solution**:

1. **Always filter by time**:
```sql
-- BAD: Full table scan
SELECT * FROM mes_core.state_log WHERE asset_id = 5;

-- GOOD: Time-bounded query
SELECT * FROM mes_core.state_log
WHERE asset_id = 5
  AND logged_at >= NOW() - INTERVAL '7 days';
```

2. **Check hypertable chunks**:
```sql
SELECT * FROM timescaledb_information.chunks
WHERE hypertable_name = 'state_log'
ORDER BY range_start DESC;
```

3. **Verify compression is working**:
```sql
SELECT hypertable_name, compressed_heap_size, compressed_total_size
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'mes_core';
```

---

### Issue: Dashboard Queries Timing Out

**Cause**: Aggregate views querying too much data.

**Solution**:

1. **Use time-bounded queries**:
```python
from mes import kpiCalc

# BAD: Large time range
dashboard = kpiCalc.getKPIDashboard("Filler 1", days=365)

# GOOD: Reasonable time range
dashboard = kpiCalc.getKPIDashboard("Filler 1", hours=8)
```

2. **Use vw_kpi_latest instead of aggregating**:
```sql
-- Fast: Pre-calculated latest values
SELECT * FROM mes_core.vw_kpi_latest
WHERE asset_id = 5;

-- Slow: Aggregating all history
SELECT kpi_name, AVG(kpi_value)
FROM mes_core.kpi_log
WHERE asset_id = 5
GROUP BY kpi_name;
```

---

### Issue: Memory Pressure During KPI Calculations

**Cause**: Calculating KPIs for too many assets at once.

**Solution**:
```python
from mes import kpiCalc, assets

# BAD: Calculate all at once
result = kpiCalc.calculateOEEForHierarchy("Plant", days=30)

# GOOD: Batch processing
assetTypes = ["Filler", "Packager", "Sealer"]
for assetType in assetTypes:
    assetList = assets.getAssetsByType(assetType)
    for asset in assetList:
        try:
            oee = kpiCalc.getOEE(asset['asset_id'], hours=8)
            print(asset['asset_name'], "OEE:", oee)
        except Exception as e:
            print(asset['asset_name'], "Error:", e)
```

---

## Connection Issues

### Issue: Database Connection Lost

**Symptoms**:
- `Connection refused` errors
- `Connection timed out` errors

**Solution**:

1. **Check Ignition database connection**:
   - Gateway > Config > Databases > Connections
   - Status should be "Valid"
   - Click "Test Connection"

2. **Verify PostgreSQL is running**:
```bash
# Check service status
systemctl status postgresql

# Check listening ports
netstat -tlnp | grep 5432
```

3. **Check connection parameters**:
```sql
-- In Ignition, verify connection works
SELECT current_database(), current_user, inet_server_addr();
```

---

### Issue: Tag Provider Not Responding

**Symptoms**:
- Tag reads return bad quality
- Tag writes fail silently

**Solution**:

1. **Check tag provider status**:
   - Gateway > Config > Tags > Realtime
   - Provider should show "Running"

2. **Restart tag provider** (if needed):
   - Gateway > Config > Tags > Realtime
   - Select provider > Restart

---

## Verification Queries

### Check System Health

```sql
-- Table record counts
SELECT 'asset_type' AS table_name, COUNT(*) FROM mes_core.asset_type
UNION ALL SELECT 'state_type', COUNT(*) FROM mes_core.state_type
UNION ALL SELECT 'state_definition', COUNT(*) FROM mes_core.state_definition
UNION ALL SELECT 'asset_definition', COUNT(*) FROM mes_core.asset_definition
UNION ALL SELECT 'state_log', COUNT(*) FROM mes_core.state_log
UNION ALL SELECT 'kpi_log', COUNT(*) FROM mes_core.kpi_log;

-- Recent activity
SELECT 'state_log' AS log_type, MAX(logged_at) AS latest FROM mes_core.state_log
UNION ALL SELECT 'production_log', MAX(logged_at) FROM mes_core.production_log
UNION ALL SELECT 'count_log', MAX(logged_at) FROM mes_core.count_log
UNION ALL SELECT 'kpi_log', MAX(logged_at) FROM mes_core.kpi_log;

-- Hypertable health
SELECT hypertable_name, num_chunks, compression_enabled
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'mes_core';
```

---

## Related Documentation

- [Deployment Checklist](./deployment-checklist.md) - Initial setup
- [Schema Reference](../05-Database/schema-reference.md) - Table structures
- [TimescaleDB Configuration](../05-Database/timescaledb-configuration.md) - Hypertable tuning
- [Gateway KPI Scripts](../02-Scripts/gateway/kpi-gateway-scripts.md) - Script troubleshooting
