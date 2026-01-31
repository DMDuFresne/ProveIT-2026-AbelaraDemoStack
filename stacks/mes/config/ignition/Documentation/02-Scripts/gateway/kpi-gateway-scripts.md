# Gateway KPI Scripts

This document describes the 11 scheduled gateway scripts that calculate and log KPIs for each equipment type in the MES system.

## Purpose

- Execute scheduled KPI calculations on a CRON schedule
- Calculate KPIs for all assets of a specific equipment type
- Write calculated values to equipment UDT tags
- Trigger database logging via LogTrigger mechanism

## Architecture Overview

```
Gateway Timer Script (CRON: 0 * * * *)
    ↓
assets.getAssetsByType(ASSET_TYPE)
    ↓
For each asset:
    ↓
kpiCalc.getXXX() functions
    ↓
system.tag.writeBlocking() → UDT Tags
    ↓
LogTrigger = True → Database via Tag Change Script
```

## Equipment Type Scripts

| Script File | Asset Type | KPIs Calculated |
|-------------|------------|-----------------|
| `kpi_script_filler.py` | Filler | OEE, Availability, Performance, Quality, MTBF, MTTR, RejectRate |
| `kpi_script_washer.py` | Washer | OEE, Availability, Performance, Quality, MTBF, MTTR |
| `kpi_script_robot.py` | Robot | OEE, Availability, Performance, MTBF, MTTR |
| `kpi_script_palletstation.py` | PalletStation | OEE, Availability, Performance, MTBF, MTTR |
| `kpi_script_caploader.py` | CapLoader | OEE, Availability, Performance, Quality, MTBF, MTTR, RejectRate |
| `kpi_script_packager.py` | Packager | OEE, Availability, Performance, Quality, MTBF, MTTR |
| `kpi_script_sealer.py` | Sealer | OEE, Availability, Performance, Quality, MTBF, MTTR |
| `kpi_script_tank.py` | Tank | Availability, MTBF, MTTR, CIPCycleEfficiency |
| `kpi_script_vat.py` | Vat | Availability, MTBF, MTTR, CIPCycleEfficiency |
| `kpi_script_labeler.py` | Labeler | OEE, Availability, Performance, Quality, MTBF, MTTR, RejectRate |
| `kpi_script_workstation.py` | Workstation | OEE, Availability, Performance, Quality |

---

## Script Pattern

All gateway scripts follow a consistent pattern:

```python
"""
Gateway Event - Scheduled Script: {AssetType} KPI Calculation
KPIs: {list of KPIs calculated}
"""
from mes import kpiCalc, assets

ASSET_TYPE = "{AssetType}"
HOURS = 8

logger = system.util.getLogger("KPI_" + ASSET_TYPE)

# Snap endTime to the exact hour boundary (floor to current hour)
now = system.date.now()
endTime = system.date.setTime(now, system.date.getHour24(now), 0, 0)
startTime = system.date.addHours(endTime, -HOURS)

assetList = assets.getAssetsByType(ASSET_TYPE)
logger.info("Processing %d %s assets" % (len(assetList), ASSET_TYPE))

for asset in assetList:
    tagPath = asset.get('tag_path')
    assetId = asset.get('asset_id')
    assetName = asset.get('asset_name', 'Unknown')

    if not tagPath:
        logger.warn("Asset '%s' has no tag_path, skipping" % assetName)
        continue

    kpis = {
        'OEE': kpiCalc.getOEE,
        'Availability': kpiCalc.getAvailability,
        'Performance': kpiCalc.getPerformanceEfficiency,
        'Quality': kpiCalc.getQualityRatio,
        'MTBF': kpiCalc.getMTBF,
        'MTTR': kpiCalc.getMTTR,
        # ... additional KPIs per equipment type
    }

    for kpiName, calcFunc in kpis.items():
        try:
            value = calcFunc(assetId, startTime=startTime, endTime=endTime)
            if value is None:
                continue

            basePath = "[MES]" + tagPath + "/KPIs/" + kpiName

            # Step 1: Write KPI values first
            valuePaths = [basePath + "/Value", basePath + "/StartTimestamp", basePath + "/EndTimestamp"]
            valueData = [value, startTime, endTime]
            results = system.tag.writeBlocking(valuePaths, valueData)

            if not all(r.isGood() for r in results):
                logger.warn("Value write failed: %s/%s" % (assetName, kpiName))
                continue

            # Step 2: Set LogTrigger AFTER values committed
            triggerResult = system.tag.writeBlocking([basePath + "/LogTrigger"], [True])

            if all(r.isGood() for r in triggerResult):
                logger.info("%s/%s = %.2f" % (assetName, kpiName, value))
            else:
                logger.warn("Trigger write failed: %s/%s" % (assetName, kpiName))
        except Exception, e:
            logger.error("%s/%s error: %s" % (assetName, kpiName, str(e)))
```

---

## Tag Path Structure

KPI values are written to the following tag structure under each equipment UDT instance:

```
[MES]{tag_path}/KPIs/
├── OEE/
│   ├── Value           (Float4)     - Calculated KPI value
│   ├── StartTimestamp  (DateTime)   - Calculation period start
│   ├── EndTimestamp    (DateTime)   - Calculation period end
│   └── LogTrigger      (Boolean)    - Set TRUE to trigger DB logging
├── Availability/
│   ├── Value
│   ├── StartTimestamp
│   ├── EndTimestamp
│   └── LogTrigger
├── Performance/
│   └── ...
├── Quality/
│   └── ...
├── MTBF/
│   └── ...
├── MTTR/
│   └── ...
└── RejectRate/          (equipment-specific)
    └── ...
```

### Example Tag Paths

```
[MES]Assets/Packaging/Line1/Filler1/KPIs/OEE/Value
[MES]Assets/Packaging/Line1/Filler1/KPIs/OEE/LogTrigger
[MES]Assets/Packaging/Line1/Filler1/KPIs/Availability/Value
```

---

## CRON Scheduling

### Recommended Schedule

| Schedule Type | CRON Expression | Use Case |
|---------------|-----------------|----------|
| Hourly | `0 * * * *` | Real-time dashboards |
| End of Shift | `0 6,14,22 * * *` | 8-hour shift reporting |
| Daily | `0 0 * * *` | Daily rollup reports |

### Gateway Timer Script Setup

1. Go to **Gateway > Config > Scripting > Gateway Timer Scripts**
2. Create a new script for each equipment type
3. Set the CRON schedule (recommended: `0 * * * *` for hourly)
4. Paste the equipment-specific script content

### Example Configuration

| Script Name | Schedule | Enabled |
|-------------|----------|---------|
| KPI_Filler | `0 * * * *` | ✓ |
| KPI_Washer | `0 * * * *` | ✓ |
| KPI_Robot | `0 * * * *` | ✓ |
| KPI_PalletStation | `0 * * * *` | ✓ |
| KPI_CapLoader | `0 * * * *` | ✓ |
| KPI_Packager | `0 * * * *` | ✓ |
| KPI_Sealer | `0 * * * *` | ✓ |
| KPI_Tank | `0 * * * *` | ✓ |
| KPI_Vat | `0 * * * *` | ✓ |
| KPI_Labeler | `0 * * * *` | ✓ |
| KPI_Workstation | `0 * * * *` | ✓ |

---

## Time Window Calculation

The scripts use **hour-aligned** time windows to ensure consistent KPI periods:

```python
# Snap endTime to the exact hour boundary
now = system.date.now()
endTime = system.date.setTime(now, system.date.getHour24(now), 0, 0)
startTime = system.date.addHours(endTime, -HOURS)
```

### Example

If script runs at 14:23:45:
- `endTime` = 14:00:00 (floored to hour)
- `startTime` = 06:00:00 (8 hours prior)
- Period = 06:00 to 14:00

This ensures:
- Consistent time boundaries for reporting
- No overlapping or missing time periods
- Clean alignment with shift schedules

---

## LogTrigger Mechanism

The **LogTrigger** tag enables database logging through a tag change script:

### Flow

```
Gateway Script: LogTrigger = True
        ↓
Tag Change Script (on LogTrigger)
        ↓
kpi.recordKPI(asset, kpiName, Value, StartTimestamp, EndTimestamp)
        ↓
INSERT INTO mes_core.kpi_log
        ↓
LogTrigger = False (reset)
```

### Tag Change Script (on LogTrigger)

```python
# Script on KPI UDT LogTrigger tag (valueChanged)
if currentValue.value == True:
    from mes import kpi

    # Read sibling tags
    basePath = tagPath.rsplit("/", 1)[0]  # Remove "/LogTrigger"
    paths = [basePath + "/Value", basePath + "/StartTimestamp", basePath + "/EndTimestamp"]
    values = system.tag.readBlocking(paths)

    kpiValue = values[0].value
    startTs = values[1].value
    endTs = values[2].value

    # Extract KPI name and asset from path
    # [MES]Assets/Area/Line/Equipment/KPIs/{KPIName}/LogTrigger
    pathParts = basePath.split("/")
    kpiName = pathParts[-1]
    equipmentPath = "/".join(pathParts[:-2])

    # Record to database
    kpi.recordKPI(equipmentPath, kpiName, kpiValue,
        startTime=startTs, endTime=endTs)

    # Reset trigger
    system.tag.writeBlocking([tagPath], [False])
```

---

## Equipment-Specific KPIs

### Production Equipment (Filler, Packager, Sealer, etc.)

| KPI | Description | Formula |
|-----|-------------|---------|
| OEE | Overall Equipment Effectiveness | A × P × Q / 10000 |
| Availability | Time-based efficiency | APT / PBT × 100 |
| Performance | Speed efficiency | Actual Rate / Ideal Rate × 100 |
| Quality | First-time quality | Good / Produced × 100 |
| MTBF | Reliability indicator | Operating Time / Failure Count |
| MTTR | Maintainability indicator | Repair Time / Repair Count |
| RejectRate | Defect rate | Reject / Produced × 100 |

### Process Equipment (Tank, Vat)

| KPI | Description | Formula |
|-----|-------------|---------|
| Availability | Time-based efficiency | APT / PBT × 100 |
| MTBF | Reliability indicator | Operating Time / Failure Count |
| MTTR | Maintainability indicator | Repair Time / Repair Count |
| CIPCycleEfficiency | Cleaning efficiency | Target CIP Time / Actual CIP Time × 100 |

### Robot/Material Handling

| KPI | Description | Formula |
|-----|-------------|---------|
| OEE | Overall effectiveness | A × P × Q / 10000 |
| Availability | Time-based efficiency | APT / PBT × 100 |
| Performance | Cycle efficiency | Actual Rate / Ideal Rate × 100 |
| MTBF | Reliability indicator | Operating Time / Failure Count |
| MTTR | Maintainability indicator | Repair Time / Repair Count |

---

## Error Handling

### Logger Levels

| Level | Usage |
|-------|-------|
| INFO | Successful KPI calculation and logging |
| WARN | Asset has no tag_path, write failures |
| ERROR | Calculation exceptions |

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `Asset 'X' has no tag_path` | Asset definition missing tag_path | Update asset_definition.tag_path in DB |
| `Value write failed` | Tag doesn't exist or bad quality | Verify UDT instance exists at path |
| `Trigger write failed` | LogTrigger tag missing | Verify KPI UDT structure |
| `MesResolutionError` | Asset not found in database | Verify asset exists with correct name |

### Log Output Examples

```
INFO  | KPI_Filler | Processing 4 Filler assets
INFO  | KPI_Filler | Filler1/OEE = 87.34
INFO  | KPI_Filler | Filler1/Availability = 94.50
WARN  | KPI_Filler | Asset 'Filler2' has no tag_path, skipping
ERROR | KPI_Filler | Filler3/Performance error: Division by zero
```

---

## Verification Queries

### Check KPI Logs

```sql
-- Recent KPI entries by asset type
SELECT
    kl.asset_name,
    kl.kpi_name,
    kl.kpi_value,
    kl.start_ts,
    kl.end_ts,
    kl.logged_at
FROM mes_core.kpi_log kl
JOIN mes_core.asset_definition ad ON ad.asset_id = kl.asset_id
JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
WHERE at.asset_type_name = 'Filler'
  AND kl.logged_at > NOW() - INTERVAL '24 hours'
ORDER BY kl.logged_at DESC;
```

### Check Assets by Type

```sql
-- Assets that should be processed by a gateway script
SELECT
    asset_id,
    asset_name,
    tag_path
FROM mes_core.asset_definition ad
JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
WHERE at.asset_type_name = 'Filler'
  AND ad.removed IS DISTINCT FROM TRUE;
```

---

## Related Documentation

- [kpiCalc Module](../domain/kpi-calc-module.md) - KPI calculation functions
- [kpi Module](../domain/kpi-module.md) - KPI CRUD operations
- [Equipment UDTs](../../03-UDTs/equipment-udts.md) - UDT tag structures
- [KPI Examples](../../06-Examples/kpi-calculation.md) - Integration examples
