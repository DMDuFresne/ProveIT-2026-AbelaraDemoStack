# KPI Reference Guide for Equipment UDTs

Standard KPI configuration for all equipment types in the ProveIT Edge Stack.

---

## Equipment Categories

Equipment is divided into two categories based on how they operate:

| Category | Equipment Types | KPI Count |
|----------|-----------------|-----------|
| **Discrete Production** | Filler, Washer, Robot, PalletStation, CapLoader, Packager, Sealer | 7 KPIs |
| **Process Vessels** | Tank, Vat | 3 KPIs |

---

## Discrete Production Equipment KPIs (7 KPIs)

These equipment types produce countable units and use all 7 standard KPIs:

| KPI Name | KPI_ID | Formula | Units | Purpose |
|----------|--------|---------|-------|---------|
| **OEE** | `1` | Availability × Performance × Quality | % | Overall equipment effectiveness |
| **Availability** | `2` | Running Time / Planned Time | % | Uptime percentage |
| **Performance** | `3` | (Actual × Ideal Cycle) / Running Time | % | Speed efficiency |
| **Quality** | `4` | GoodCount / InfeedCount | % | First-pass yield |
| **MTBF** | `5` | Running Time / # Failures | hours | Mean time between failures |
| **MTTR** | `6` | Total Repair Time / # Failures | hours | Mean time to repair |
| **RejectRate** | `10` | ScrapCount / InfeedCount | % | Defect/scrap percentage |

**Equipment using 7 KPIs:**
- Filler (`Models/Equipment/Process/Filler`)
- Washer (`Models/Equipment/Process/Washer`)
- Robot (`Models/Equipment/Process/Robot`)
- PalletStation (`Models/Equipment/Process/PalletStation`)
- CapLoader (`Models/Equipment/Process/CapLoader`)
- Packager (`Models/Equipment/Process/Packager`)
- Sealer (`Models/Equipment/Process/Sealer`)

---

## Process Vessel KPIs (3 KPIs)

Tanks and Vats are **batch/continuous process vessels**, not discrete production equipment.
They don't produce countable units, so count-based KPIs (OEE, Performance, Quality, RejectRate) are not applicable.

| KPI Name | KPI_ID | Formula | Units | Purpose |
|----------|--------|---------|-------|---------|
| **Availability** | `2` | Running Time / Planned Time | % | Uptime percentage |
| **MTBF** | `5` | Running Time / # Failures | hours | Mean time between failures |
| **MTTR** | `6` | Total Repair Time / # Failures | hours | Mean time to repair |

**Equipment using 3 KPIs:**
- Tank (`Models/Equipment/Process/Tank`)
- Vat (`Models/Equipment/Process/Vat`)

### Why Process Vessels Have Fewer KPIs

The `kpiCalc.py` calculation functions require:
- **Performance**: Actual Rate / Ideal Rate based on **cycle times** and **produced quantities**
- **Quality**: GoodCount / ProducedCount (requires **discrete countable output**)
- **OEE**: Availability × Performance × Quality (depends on the above)

Tanks and Vats don't have these inputs - they hold product, regulate temperature/pressure, but don't "produce" discrete units.

---

## Quick Reference

```
KPI_ID  KPI Name        Discrete  Process Vessel
------  --------------  --------  --------------
  1     OEE             ✓
  2     Availability    ✓         ✓
  3     Performance     ✓
  4     Quality         ✓
  5     MTBF            ✓         ✓
  6     MTTR            ✓         ✓
 10     RejectRate      ✓
```

---

## KPI Instance Template

When adding a KPI to a UDT in Ignition Designer:

```json
{
  "name": "<KPI_NAME>",
  "tagType": "UdtInstance",
  "tags": [
    {"name": "Id", "tagType": "AtomicTag", "value": <KPI_ID>},
    {"name": "Formula", "tagType": "AtomicTag"},
    {"name": "UnitsOfMeasure", "tagType": "AtomicTag"},
    {"name": "StartTimestamp", "tagType": "AtomicTag"},
    {"name": "Value", "tagType": "AtomicTag"},
    {"name": "EndTimestamp", "tagType": "AtomicTag"},
    {"name": "Name", "tagType": "AtomicTag"},
    {"name": "LogTrigger", "tagType": "AtomicTag"},
    {"name": "LogId", "tagType": "AtomicTag"}
  ],
  "typeId": "Models/Objects/KPI"
}
```

---

## Complete KPIs Folder Templates

### For Discrete Production Equipment (7 KPIs)

```json
{
  "name": "KPIs",
  "tagType": "Folder",
  "tags": [
    {
      "name": "OEE",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 1}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "Availability",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 2}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "Performance",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 3}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "Quality",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 4}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "MTBF",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 5}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "MTTR",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 6}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "RejectRate",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 10}],
      "typeId": "Models/Objects/KPI"
    }
  ]
}
```

### For Process Vessels (3 KPIs)

```json
{
  "name": "KPIs",
  "tagType": "Folder",
  "tags": [
    {
      "name": "Availability",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 2}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "MTBF",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 5}],
      "typeId": "Models/Objects/KPI"
    },
    {
      "name": "MTTR",
      "tagType": "UdtInstance",
      "tags": [{"name": "Id", "tagType": "AtomicTag", "value": 6}],
      "typeId": "Models/Objects/KPI"
    }
  ]
}
```

---

## Adding KPIs in Ignition Designer

1. Open the UDT definition in Tag Browser
2. Navigate to (or create) the `KPIs` folder
3. Right-click → **Add UDT Instance**
4. Select `Models/Objects/KPI`
5. Name it exactly using the KPI name from the tables above
6. Set the `Id` tag to the correct KPI_ID
7. The Name, Formula, and UnitsOfMeasure auto-populate from the database

---

## Database Verification

### Check KPI Definitions Exist

```sql
SELECT kpi_id, kpi_name, kpi_unit, kpi_formula
FROM mes_core.kpi_definition
WHERE kpi_id IN (1, 2, 3, 4, 5, 6, 10)
ORDER BY kpi_id;
```

### Check KPI Logging

```sql
SELECT
    kd.kpi_name,
    COUNT(*) as records,
    ROUND(AVG(kl.kpi_value)::numeric, 2) as avg_value,
    MAX(kl.created_at) as last_logged
FROM mes_core.kpi_log kl
JOIN mes_core.kpi_definition kd ON kl.kpi_id = kd.kpi_id
WHERE kd.kpi_id IN (1, 2, 3, 4, 5, 6, 10)
GROUP BY kd.kpi_name
ORDER BY kd.kpi_name;
```

---

## Deprecated KPIs (Not Used)

These KPIs were removed from the standard set:

| KPI_ID | KPI Name | Reason |
|--------|----------|--------|
| 7 | BottleneckIndicator | Line-level metric, not equipment-level |
| 8 | CIPCycleEfficiency | No CIP state tracking in database |
| 9 | OverfillWaste | No overfill measurement type in database |

---

## Summary

### Discrete Production Equipment (7 KPIs)
| KPI | ID |
|-----|-----|
| OEE | **1** |
| Availability | **2** |
| Performance | **3** |
| Quality | **4** |
| MTBF | **5** |
| MTTR | **6** |
| RejectRate | **10** |

### Process Vessels (3 KPIs)
| KPI | ID |
|-----|-----|
| Availability | **2** |
| MTBF | **5** |
| MTTR | **6** |
