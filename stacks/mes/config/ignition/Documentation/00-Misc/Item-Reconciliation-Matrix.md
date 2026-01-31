# Item Management 3-Way Reconciliation Matrix

**Document Purpose:** Compare item/product data across three data sources to identify discrepancies and alignment gaps.

**Generated:** 2026-01-24

---

## Data Sources

| Source | Records | Primary Key | Description |
|--------|---------|-------------|-------------|
| Pilot Database Export | 22 items | `itemid` | Master item definitions with BOM hierarchy |
| QuestDB/UNS Historical | 14 items | `itemid` | Items observed in production (last 12h) |
| MES Core Database | 10 products | `product_id` | Production execution product definitions |

---

## Complete 3-Way Mapping Table

| Pilot ID | Pilot Name | QuestDB ID | QuestDB Name | MES ID | MES Name | Status |
|----------|------------|------------|--------------|--------|----------|--------|
| 1 | Orange Soda Mix | 1 | Orange Soda Mix | 2 | Orange Soda Mix | **ID MISMATCH** |
| 2 | Cola Mix | 2 | Cola Mix | 1 | Cola Mix | **ID MISMATCH** |
| 3 | Orange Soda 0.5L | 3 | Orange Soda 0.5L | 4 | Orange Soda 0.5L | **ID MISMATCH** |
| 4 | Cola Soda 0.5L | 4 | Cola Soda 0.5L | 3 | Cola Soda 0.5L | **ID MISMATCH** |
| 5 | Orange 0.5L 4Pk | 5 | Orange 0.5L 4Pk | - | - | **MISSING IN MES** |
| 6 | Orange 0.5L 6Pk | 6 | Orange 0.5L 6Pk | 10 | Orange 0.5L 6Pk | **ID MISMATCH** |
| 7 | Orange 0.5L 12Pk | 7 | Orange 0.5L 12Pk | - | - | **MISSING IN MES** |
| 8 | Orange 0.5L 16Pk | 8 | Orange 0.5L 16Pk | 9 | Orange 0.5L 16Pk | **ID MISMATCH** |
| 9 | Orange 0.5L 20Pk | 9 | Orange 0.5L 20Pk | - | - | **MISSING IN MES** |
| 10 | Orange 0.5L 24Pk | 10 | Orange 0.5L 24Pk | 8 | Orange 0.5L 24Pk | **ID MISMATCH** |
| 11 | Cola 0.5L 4Pk Standard | - | (not observed) | - | - | **MISSING IN MES** |
| 12 | Cola 0.5L 6Pk Standard | 12 | Cola 0.5L 6Pk | 7 | Cola 0.5L 6Pk | **ID MISMATCH** |
| 13 | Cola 0.5L 12Pk Standard | - | (not observed) | - | - | **MISSING IN MES** |
| 14 | Cola 0.5L 16Pk Standard | 14 | Cola 0.5L 16Pk | 6 | Cola 0.5L 16Pk | **ID MISMATCH** |
| 15 | Cola 0.5L 20Pk Standard | 15 | Cola 0.5L 20Pk | - | - | **MISSING IN MES** |
| 16 | Cola 0.5L 24Pk Standard | 16 | Cola 0.5L 24Pk | 5 | Cola 0.5L 24Pk | **ID MISMATCH** |
| 17 | Cola 0.5L 4Pk Seasonal | - | (not observed) | - | - | **MISSING IN MES** |
| 18 | Cola 0.5L 6Pk Seasonal | - | (not observed) | - | - | **MISSING IN MES** |
| 19 | Cola 0.5L 12Pk Seasonal | - | (not observed) | - | - | **MISSING IN MES** |
| 20 | Cola 0.5L 16Pk Seasonal | - | (not observed) | - | - | **MISSING IN MES** |
| 21 | Cola 0.5L 20Pk Seasonal | - | (not observed) | - | - | **MISSING IN MES** |
| 22 | Cola 0.5L 24Pk Seasonal | - | (not observed) | - | - | **MISSING IN MES** |

---

## Reconciliation Summary

### Status Counts

| Status | Count | Percentage |
|--------|-------|------------|
| ID MISMATCH (name matches, ID differs) | 10 | 45% |
| MISSING IN MES | 12 | 55% |
| FULL MATCH | 0 | 0% |
| **Total Items** | **22** | 100% |

### QuestDB Observation Coverage

| Category | Count | Notes |
|----------|-------|-------|
| Items observed in production | 14 | Active in last 12 hours |
| Items not observed | 8 | IDs: 11, 13, 17-22 |

---

## Critical Issues

### Issue 1: ID Misalignment Between Pilot/UNS and MES Core

**Severity:** CRITICAL

All products that exist in both systems have different IDs. This breaks referential integrity for:
- Work order tracking
- Production reporting
- Quality traceability
- Inventory reconciliation

| Product | Pilot/QuestDB ID | MES Core ID | Delta |
|---------|------------------|-------------|-------|
| Orange Soda Mix | 1 | 2 | +1 |
| Cola Mix | 2 | 1 | -1 |
| Orange Soda 0.5L | 3 | 4 | +1 |
| Cola Soda 0.5L | 4 | 3 | -1 |
| Orange 0.5L 6Pk | 6 | 10 | +4 |
| Orange 0.5L 16Pk | 8 | 9 | +1 |
| Orange 0.5L 24Pk | 10 | 8 | -2 |
| Cola 0.5L 6Pk | 12 | 7 | -5 |
| Cola 0.5L 16Pk | 14 | 6 | -8 |
| Cola 0.5L 24Pk | 16 | 5 | -11 |

**Root Cause Hypothesis:** Systems were set up independently with different auto-increment sequences or manual ID assignments.

---

### Issue 2: Missing Products in MES Core

**Severity:** HIGH

12 products defined in Pilot are not configured in MES Core:

| Category | Missing Products | Impact |
|----------|------------------|--------|
| Pack sizes 4, 12, 20 | 6 items | Cannot schedule/track these pack configurations |
| Seasonal variants | 6 items | Cannot differentiate seasonal from standard production |

**Missing Pack Configurations:**
- 4-Pack: Orange, Cola Standard, Cola Seasonal
- 12-Pack: Orange, Cola Standard, Cola Seasonal
- 20-Pack: Orange, Cola Standard, Cola Seasonal

**Missing Seasonal Line (all Cola 0.5L):**
- 4Pk, 6Pk, 12Pk, 16Pk, 20Pk, 24Pk Seasonal variants

---

### Issue 3: Schema Differences

| Attribute | Pilot | QuestDB | MES Core | Gap |
|-----------|-------|---------|----------|-----|
| `parentitemid` (BOM) | Yes | No | No | MES cannot represent BOM hierarchy |
| `bottlesize` | Yes | No | No | Bottle size not tracked in MES |
| `labelvariant` | Yes | No | No | Label variant not tracked in MES |
| `packcount` | Yes | No | No | Pack count not tracked in MES |
| `unit_of_measure` | No | No | Yes | Pilot missing UoM |
| `ideal_cycle_time` | No | No | Yes | Pilot missing engineering data |
| `tolerance_pct` | No | No | Yes | Pilot missing tolerance specs |

---

## BOM Hierarchy (Pilot Only)

The Pilot database maintains a Bill of Materials hierarchy via `parentitemid`:

```
Mix (Level 0)
├── Orange Soda Mix (ID: 1)
│   └── Orange Soda 0.5L (ID: 3) [Bottle]
│       ├── Orange 0.5L 4Pk (ID: 5)
│       ├── Orange 0.5L 6Pk (ID: 6)
│       ├── Orange 0.5L 12Pk (ID: 7)
│       ├── Orange 0.5L 16Pk (ID: 8)
│       ├── Orange 0.5L 20Pk (ID: 9)
│       └── Orange 0.5L 24Pk (ID: 10)
│
└── Cola Mix (ID: 2)
    └── Cola Soda 0.5L (ID: 4) [Bottle]
        ├── Standard Packs (IDs: 11-16)
        │   ├── Cola 0.5L 4Pk (ID: 11)
        │   ├── Cola 0.5L 6Pk (ID: 12)
        │   ├── Cola 0.5L 12Pk (ID: 13)
        │   ├── Cola 0.5L 16Pk (ID: 14)
        │   ├── Cola 0.5L 20Pk (ID: 15)
        │   └── Cola 0.5L 24Pk (ID: 16)
        │
        └── Seasonal Packs (IDs: 17-22)
            ├── Cola 0.5L 4Pk Seasonal (ID: 17)
            ├── Cola 0.5L 6Pk Seasonal (ID: 18)
            ├── Cola 0.5L 12Pk Seasonal (ID: 19)
            ├── Cola 0.5L 16Pk Seasonal (ID: 20)
            ├── Cola 0.5L 20Pk Seasonal (ID: 21)
            └── Cola 0.5L 24Pk Seasonal (ID: 22)
```

**Note:** MES Core uses `product_family` (Mix/Bottle/Pack) but cannot represent parent-child relationships.

---

## Recommendations

### Priority 1: Create Linking Tables in `mes_custom` (Immediate)

Create cross-reference and extended attribute tables in the `mes_custom` schema to bridge the gap between Pilot/UNS and MES Core without modifying core schemas.

#### Table 1: `mes_custom.item_xref` - Core ID Mapping

Maps Pilot item IDs to MES Core product IDs and tracks sync status.

```sql
CREATE TABLE mes_custom.item_xref (
    pilot_item_id      INT PRIMARY KEY,
    pilot_item_name    VARCHAR(100) NOT NULL,
    mes_product_id     INT REFERENCES mes_core.product_definition(product_id),
    sync_status        VARCHAR(20) DEFAULT 'mapped',
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_sync_status CHECK (sync_status IN ('mapped', 'missing', 'deprecated'))
);

COMMENT ON TABLE mes_custom.item_xref IS 'Cross-reference linking Pilot item IDs to MES Core product IDs';
COMMENT ON COLUMN mes_custom.item_xref.sync_status IS 'mapped=exists in both, missing=Pilot only, deprecated=no longer used';
```

#### Table 2: `mes_custom.item_extended_attributes` - Schema Gap Filler

Stores Pilot-specific attributes not present in MES Core (BOM hierarchy, label variants, etc.).

```sql
CREATE TABLE mes_custom.item_extended_attributes (
    pilot_item_id      INT PRIMARY KEY REFERENCES mes_custom.item_xref(pilot_item_id),
    parent_item_id     INT REFERENCES mes_custom.item_xref(pilot_item_id),
    item_class         VARCHAR(20),
    bottle_size        VARCHAR(20),
    label_variant      VARCHAR(50),
    pack_count         INT,

    CONSTRAINT chk_item_class CHECK (item_class IN ('Mix', 'Bottle', 'Pack'))
);

COMMENT ON TABLE mes_custom.item_extended_attributes IS 'Extended attributes from Pilot not available in MES Core';
COMMENT ON COLUMN mes_custom.item_extended_attributes.parent_item_id IS 'BOM hierarchy - references parent item for Pack->Bottle->Mix relationship';
```

#### Initial Data Population

```sql
-- Insert all 22 Pilot items with their MES Core mappings
INSERT INTO mes_custom.item_xref (pilot_item_id, pilot_item_name, mes_product_id, sync_status) VALUES
(1,  'Orange Soda Mix',           2,    'mapped'),
(2,  'Cola Mix',                  1,    'mapped'),
(3,  'Orange Soda 0.5L',          4,    'mapped'),
(4,  'Cola Soda 0.5L',            3,    'mapped'),
(5,  'Orange 0.5L 4Pk',           NULL, 'missing'),
(6,  'Orange 0.5L 6Pk',           10,   'mapped'),
(7,  'Orange 0.5L 12Pk',          NULL, 'missing'),
(8,  'Orange 0.5L 16Pk',          9,    'mapped'),
(9,  'Orange 0.5L 20Pk',          NULL, 'missing'),
(10, 'Orange 0.5L 24Pk',          8,    'mapped'),
(11, 'Cola 0.5L 4Pk Standard',    NULL, 'missing'),
(12, 'Cola 0.5L 6Pk Standard',    7,    'mapped'),
(13, 'Cola 0.5L 12Pk Standard',   NULL, 'missing'),
(14, 'Cola 0.5L 16Pk Standard',   6,    'mapped'),
(15, 'Cola 0.5L 20Pk Standard',   NULL, 'missing'),
(16, 'Cola 0.5L 24Pk Standard',   5,    'mapped'),
(17, 'Cola 0.5L 4Pk Seasonal',    NULL, 'missing'),
(18, 'Cola 0.5L 6Pk Seasonal',    NULL, 'missing'),
(19, 'Cola 0.5L 12Pk Seasonal',   NULL, 'missing'),
(20, 'Cola 0.5L 16Pk Seasonal',   NULL, 'missing'),
(21, 'Cola 0.5L 20Pk Seasonal',   NULL, 'missing'),
(22, 'Cola 0.5L 24Pk Seasonal',   NULL, 'missing');

-- Insert extended attributes with BOM hierarchy
INSERT INTO mes_custom.item_extended_attributes
(pilot_item_id, parent_item_id, item_class, bottle_size, label_variant, pack_count) VALUES
(1,  0,    'Mix',    NULL,    NULL,       NULL),
(2,  0,    'Mix',    NULL,    NULL,       NULL),
(3,  1,    'Bottle', '0.5L',  NULL,       NULL),
(4,  2,    'Bottle', '0.5L',  NULL,       NULL),
(5,  3,    'Pack',   '0.5L',  NULL,       4),
(6,  3,    'Pack',   '0.5L',  NULL,       6),
(7,  3,    'Pack',   '0.5L',  NULL,       12),
(8,  3,    'Pack',   '0.5L',  NULL,       16),
(9,  3,    'Pack',   '0.5L',  NULL,       20),
(10, 3,    'Pack',   '0.5L',  NULL,       24),
(11, 4,    'Pack',   '0.5L',  'Standard', 4),
(12, 4,    'Pack',   '0.5L',  'Standard', 6),
(13, 4,    'Pack',   '0.5L',  'Standard', 12),
(14, 4,    'Pack',   '0.5L',  'Standard', 16),
(15, 4,    'Pack',   '0.5L',  'Standard', 20),
(16, 4,    'Pack',   '0.5L',  'Standard', 24),
(17, 4,    'Pack',   '0.5L',  'Seasonal', 4),
(18, 4,    'Pack',   '0.5L',  'Seasonal', 6),
(19, 4,    'Pack',   '0.5L',  'Seasonal', 12),
(20, 4,    'Pack',   '0.5L',  'Seasonal', 16),
(21, 4,    'Pack',   '0.5L',  'Seasonal', 20),
(22, 4,    'Pack',   '0.5L',  'Seasonal', 24);
```

#### Utility Views

```sql
-- View: Complete item mapping with all attributes
CREATE VIEW mes_custom.v_item_complete AS
SELECT
    x.pilot_item_id,
    x.pilot_item_name,
    x.mes_product_id,
    p.product_name AS mes_product_name,
    x.sync_status,
    e.parent_item_id,
    parent.pilot_item_name AS parent_item_name,
    e.item_class,
    e.bottle_size,
    e.label_variant,
    e.pack_count,
    p.unit_of_measure,
    p.ideal_cycle_time_seconds
FROM mes_custom.item_xref x
LEFT JOIN mes_core.product_definition p ON x.mes_product_id = p.product_id
LEFT JOIN mes_custom.item_extended_attributes e ON x.pilot_item_id = e.pilot_item_id
LEFT JOIN mes_custom.item_xref parent ON e.parent_item_id = parent.pilot_item_id;

-- View: Missing items that need to be added to MES Core
CREATE VIEW mes_custom.v_items_missing_in_mes AS
SELECT
    x.pilot_item_id,
    x.pilot_item_name,
    e.item_class,
    e.pack_count,
    e.label_variant
FROM mes_custom.item_xref x
JOIN mes_custom.item_extended_attributes e ON x.pilot_item_id = e.pilot_item_id
WHERE x.sync_status = 'missing';

-- Function: Translate Pilot ID to MES ID
CREATE OR REPLACE FUNCTION mes_custom.get_mes_product_id(p_pilot_item_id INT)
RETURNS INT AS $$
    SELECT mes_product_id FROM mes_custom.item_xref WHERE pilot_item_id = p_pilot_item_id;
$$ LANGUAGE SQL STABLE;

-- Function: Translate MES ID to Pilot ID
CREATE OR REPLACE FUNCTION mes_custom.get_pilot_item_id(p_mes_product_id INT)
RETURNS INT AS $$
    SELECT pilot_item_id FROM mes_custom.item_xref WHERE mes_product_id = p_mes_product_id;
$$ LANGUAGE SQL STABLE;
```

#### Design Benefits

| Problem | Solution |
|---------|----------|
| ID mismatch between systems | `item_xref` provides bidirectional lookup |
| Missing products in MES Core | `sync_status = 'missing'` flags gaps for future action |
| BOM hierarchy not in MES | `item_extended_attributes.parent_item_id` preserves structure |
| Schema attribute gaps | Extended attributes table holds Pilot-only fields |
| No core schema changes | All tables in `mes_custom` - MES Core untouched |
| Query convenience | Views and functions simplify integration logic |

---

### Priority 2: Add Missing Products to MES Core (Short-term)

Once linking tables are in place, add the 12 missing products to `mes_core.product_definition`:

```sql
-- Use the missing items view to generate inserts
INSERT INTO mes_core.product_definition
(product_name, product_family_id, unit_of_measure, is_active)
SELECT
    pilot_item_name,
    CASE item_class
        WHEN 'Mix' THEN 1
        WHEN 'Bottle' THEN 2
        WHEN 'Pack' THEN 3
    END,
    CASE item_class
        WHEN 'Mix' THEN 'batch'
        WHEN 'Bottle' THEN 'ea'
        WHEN 'Pack' THEN 'pack'
    END,
    TRUE
FROM mes_custom.v_items_missing_in_mes;

-- Then update item_xref with new MES IDs and set sync_status = 'mapped'
```

### Priority 3: Align IDs at Source (Long-term)

Choose one system as the "golden source" for item IDs and migrate the others:

| Option | Effort | Risk | Recommendation |
|--------|--------|------|----------------|
| A: Pilot IDs are master | Medium | Low | **Recommended** - most complete data |
| B: MES IDs are master | High | Medium | Requires Pilot/UNS reconfiguration |
| C: New unified IDs | Very High | High | Not recommended |

### Priority 4: Schema Harmonization (Long-term)

1. Add `unit_of_measure` to Pilot schema
2. Add `parent_product_id` to MES Core schema
3. Create shared data dictionary for common attributes

---

## Appendix A: Source Data Details

### Pilot Database Export
- **File:** `Enterprise B/Pilot Database Export/ProveIt - Enterprise B - itemmanagement 2026-01-19 15-37-08.json`
- **Export Date:** 2026-01-19 15:37:08
- **Record Count:** 22 items

### QuestDB Topics Analyzed
- `Enterprise B/Site1/*/workorder/lotnumber/item/itemid`
- `Enterprise B/Site1/*/workorder/lotnumber/item/itemname`
- **Time Range:** Last 12 hours
- **Unique Items Observed:** 14

### MES Core Tables
- `mes_core.product_definition` (10 records)
- `mes_core.product_family` (3 records: Mix, Bottle, Pack)

---

## Appendix B: ID Cross-Reference Quick Lookup

| Product Name | Pilot ID | MES ID | Match? |
|--------------|----------|--------|--------|
| Cola Mix | 2 | 1 | No |
| Cola Soda 0.5L | 4 | 3 | No |
| Cola 0.5L 24Pk | 16 | 5 | No |
| Cola 0.5L 16Pk | 14 | 6 | No |
| Cola 0.5L 6Pk | 12 | 7 | No |
| Orange 0.5L 24Pk | 10 | 8 | No |
| Orange 0.5L 16Pk | 8 | 9 | No |
| Orange 0.5L 6Pk | 6 | 10 | No |
| Orange Soda Mix | 1 | 2 | No |
| Orange Soda 0.5L | 3 | 4 | No |

---

*Document maintained by: Data Integration Team*
*Next Review: 2026-02-24*
