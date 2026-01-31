# State Reconciliation Matrix: QuestDB (Enterprise B) ↔ MES Core (Postgres)

> Generated: 2026-01-24

## Complete Mapping Table

| Code | QuestDB State Name | QuestDB Type | 24h Count | MES State ID | MES State Name | MES Type | Downtime? |
|:----:|-------------------|--------------|----------:|:------------:|----------------|----------|:---------:|
| 0 | Running | Running | 121,431 | 6 | Running (Code 0) | Running | No |
| 1 | Pasteurize | Running | 2,209 | 5 | Pasteurize (Code 1) | Running | No |
| 2 | Cool | Running | 1,415 | 4 | Cool (Code 2) | Running | No |
| 3 | Fill | Running | 3,469 | 3 | Fill (Code 3) | Running | No |
| 4 | Mix | Running | 3,032 | 2 | Mix (Code 4) | Running | No |
| 5 | Transfer | Running | 2,193 | 1 | Transfer (Code 5) | Running | No |
| 100 | Unplanned Downtime | UnplannedDowntime | 2,999 | 11 | Unplanned Downtime (Code 100) | UnplannedDowntime | **Yes** |
| 200 | Idle | Idle | 43,308 | 13 | Idle (Code 200) | Idle | No |
| 202 | Blocked | Idle | 1,560 | 14 | Blocked (Code 202) | Blocked | **Yes** |
| 300 | Planned Downtime | PlannedDowntime | 3,271 | 10 | PlannedDowntime (Code 300) | PlannedDowntime | **Yes** |
| 301 | Changeover | PlannedDowntime | 738 | 9 | Changeover (Code 301) | PlannedDowntime | **Yes** |
| 305 | CIP | PlannedDowntime | 2,747 | 8 | CIP (Code 305) | PlannedDowntime | **Yes** |
| 306 | Cleaning | PlannedDowntime | 1,362 | 7 | Cleaning (Code 306) | PlannedDowntime | **Yes** |
| — | Unknown | Unknown | 34,559 | 12 | Unknown / Unmapped | UnplannedDowntime | **Yes** |

---

## State Code Reference

| Code Range | Category | States Included |
|:----------:|----------|-----------------|
| 0-5 | Running (Production) | Running, Pasteurize, Cool, Fill, Mix, Transfer |
| 100-199 | Unplanned Downtime | Unplanned Downtime (100) |
| 200-299 | Idle/Blocked | Idle (200), Blocked (202) |
| 300-399 | Planned Downtime | Planned Downtime (300), Changeover (301), CIP (305), Cleaning (306) |

---

## MES Core State Types (Canonical Reference)

| Type ID | Type Name | Description | Downtime? |
|:-------:|-----------|-------------|:---------:|
| 1 | Running | Actively executing production | No |
| 2 | PlannedDowntime | Scheduled stops (CIP, changeover, cleaning) | Yes |
| 3 | UnplannedDowntime | Faults or unplanned stops | Yes |
| 4 | Idle | Standby/available, no demand | No |
| 5 | Blocked | Downstream constraint | Yes |

---

## MES Core State Definitions (Full List)

| State ID | Type ID | State Name | Description | Color |
|:--------:|:-------:|------------|-------------|-------|
| 1 | 1 | Transfer (Code 5) | Transfer in progress (vat to tank, tank to filler feed) | #2ECC71 |
| 2 | 1 | Mix (Code 4) | Mixing or batching active (vats) | #2ECC71 |
| 3 | 1 | Fill (Code 3) | Filling and capping active | #2ECC71 |
| 4 | 1 | Cool (Code 2) | Cooling step active (where applicable) | #2ECC71 |
| 5 | 1 | Pasteurize (Code 1) | Pasteurization step active (where applicable) | #2ECC71 |
| 6 | 1 | Running (Code 0) | Generic running state when no sub-state is provided | #2ECC71 |
| 7 | 2 | Cleaning (Code 306) | Non-CIP cleaning or sanitation | #3498DB |
| 8 | 2 | CIP (Code 305) | Clean-in-place cycle | #3498DB |
| 9 | 2 | Changeover (Code 301) | Product or format changeover | #3498DB |
| 10 | 2 | PlannedDowntime (Code 300) | Generic planned stop | #3498DB |
| 11 | 3 | Unplanned Downtime (Code 100) | Faulted or unplanned stop event | #E74C3C |
| 12 | 3 | Unknown / Unmapped | Used only for data-quality handling when source reports UNKNOWN | #E74C3C |
| 13 | 4 | Idle (Code 200) | Asset is stopped but available | #95A5A6 |
| 14 | 5 | Blocked (Code 202) | Asset prevented from running due to downstream stop or backpressure | #E67E22 |

### Duplicate/Legacy Definitions (Recommend Deprecation)

| State ID | Type ID | State Name | Notes |
|:--------:|:-------:|------------|-------|
| 55 | 1 | Running | Duplicate of ID 6, null description, gray color |
| 56 | 4 | Idle | Duplicate of ID 13, null description, gray color |
| 57 | 48 | Planned Downtime | Duplicate of ID 10, uses generic "Downtime" type |
| 58 | 48 | Unplanned Downtime | Duplicate of ID 11, uses generic "Downtime" type |

---

## Issues Identified

### High Priority

| Issue | Details | Recommendation |
|-------|---------|----------------|
| 15.5% Unknown states | 34,559 records with no valid state code | Investigate PLC/gateway communication; implement alerting |
| Blocked type mismatch | QuestDB classifies as `Idle`, MES Core as `Blocked` with `is_downtime=true` | Align QuestDB type classification |

### Medium Priority

| Issue | Details | Recommendation |
|-------|---------|----------------|
| Duplicate MES definitions | State IDs 55-58 duplicate IDs 6, 13, 10, 11 | Deprecate IDs 55-58; standardize on IDs 1-14 |
| Unknown lacks code | No explicit code assigned in QuestDB | Assign explicit code (e.g., -1 or 999) |

### Low Priority

| Issue | Details | Recommendation |
|-------|---------|----------------|
| Color standardization | State IDs 55-58 use gray (#D5D5D5) | Apply functional colors after consolidation |

---

## Data Quality Summary

| Metric | Value | Status |
|--------|------:|:------:|
| Total records (24h) | 224,008 | - |
| Valid mapped states | 189,449 | 84.5% |
| Unknown/Unmapped | 34,559 | 15.5% |
| Code-to-Name consistency | 100% | GOOD |
| Type classification alignment | 92% | NEEDS REVIEW |
| MES duplicate definitions | 4 pairs | NEEDS CLEANUP |

---

## Data Sources

- **QuestDB**: `mqtt_messages` table (Enterprise B historical data)
- **PostgreSQL**: `mes_core.state_definition` and `mes_core.state_type` tables
- **Neo4j**: UNS topic hierarchy for state path discovery
