-- ============================================================================
-- Custom Schema: Pilot/UNS Reconciliation Tables
-- Database: proveit-mes
-- Schema: mes_custom
--
-- Purpose: Bridge Pilot/UNS codes to MES Core IDs using name-based lookups.
--          This file is self-contained and does not depend on specific ID values.
--
-- Dependencies:
--   - mes_core.state_definition (from seed data)
--   - mes_core.product_definition (from seed data)
--
-- Author(s): Dylan DuFresne
-- Generated: 2026-01-25
-- ============================================================================

-- ============================================================================
-- CUSTOM SCHEMA VERSION TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS mes_custom.custom_schema_version (
    version_id      SERIAL PRIMARY KEY,
    version         VARCHAR(20) NOT NULL,
    description     TEXT,
    applied_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE mes_custom.custom_schema_version IS 'Tracks custom schema versions applied to this database';

-- ============================================================================
-- SECTION 1: STATE RECONCILIATION
-- Purpose: Bridge Pilot/UNS state codes to MES Core state IDs
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: state_xref - Pilot State Code to MES State ID Mapping
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mes_custom.state_xref (
    pilot_state_code    INT PRIMARY KEY,
    pilot_state_name    VARCHAR(50) NOT NULL,
    pilot_state_type    VARCHAR(30) NOT NULL,
    mes_state_id        BIGINT NOT NULL REFERENCES mes_core.state_definition(state_id),
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE mes_custom.state_xref IS 'Cross-reference linking Pilot/UNS state codes to MES Core state IDs';
COMMENT ON COLUMN mes_custom.state_xref.pilot_state_code IS 'State code from Pilot/UNS (e.g., 0=Running, 100=Unplanned)';
COMMENT ON COLUMN mes_custom.state_xref.pilot_state_type IS 'Type classification from Pilot (Running, Idle, PlannedDowntime, etc.)';

-- ----------------------------------------------------------------------------
-- Initial Data: state_xref (14 state codes including Unknown)
-- Uses name-based lookups to find state_id values dynamically
-- ----------------------------------------------------------------------------
INSERT INTO mes_custom.state_xref
    (pilot_state_code, pilot_state_name, pilot_state_type, mes_state_id, notes)
SELECT
    v.pilot_state_code,
    v.pilot_state_name,
    v.pilot_state_type,
    sd.state_id,
    v.notes
FROM (VALUES
    -- Running states (Pilot codes 0-5)
    (0,   'Running',            'Running',           'Running',            NULL::TEXT),
    (1,   'Pasteurize',         'Running',           'Pasteurize',         NULL),
    (2,   'Cool',               'Running',           'Cool',               NULL),
    (3,   'Fill',               'Running',           'Fill',               NULL),
    (4,   'Mix',                'Running',           'Mix',                NULL),
    (5,   'Transfer',           'Running',           'Transfer',           NULL),
    -- Unplanned Downtime (Pilot code 100)
    (100, 'Unplanned Downtime', 'UnplannedDowntime', 'Unplanned Downtime', NULL),
    -- Idle/Blocked (Pilot codes 200-299)
    (200, 'Idle',               'Idle',              'Idle',               NULL),
    (202, 'Blocked',            'Idle',              'Blocked',            'Pilot classifies as Idle, MES Core as Blocked (is_downtime=true)'),
    -- Planned Downtime (Pilot codes 300-399)
    (300, 'Planned Downtime',   'PlannedDowntime',   'Planned Downtime',   NULL),
    (301, 'Changeover',         'PlannedDowntime',   'Changeover',         NULL),
    (305, 'CIP',                'PlannedDowntime',   'CIP',                NULL),
    (306, 'Cleaning',           'PlannedDowntime',   'Cleaning',           NULL),
    -- Unknown (using -1 as code placeholder)
    (-1,  'Unknown',            'Unknown',           'Unknown',            '15.5% of records - investigate PLC/gateway communication')
) AS v(pilot_state_code, pilot_state_name, pilot_state_type, mes_state_name, notes)
JOIN mes_core.state_definition sd ON sd.state_name = v.mes_state_name
ON CONFLICT (pilot_state_code) DO UPDATE SET
    pilot_state_name = EXCLUDED.pilot_state_name,
    pilot_state_type = EXCLUDED.pilot_state_type,
    mes_state_id = EXCLUDED.mes_state_id,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- View: v_state_complete - Full state mapping with MES Core details
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mes_custom.v_state_complete AS
SELECT
    x.pilot_state_code,
    x.pilot_state_name,
    x.pilot_state_type,
    x.mes_state_id,
    sd.state_name AS mes_state_name,
    st.state_type_name AS mes_state_type,
    st.is_downtime,
    sd.state_color,
    x.notes,
    CASE
        WHEN x.pilot_state_type = st.state_type_name THEN 'aligned'
        WHEN x.pilot_state_type = 'Idle' AND st.state_type_name = 'Blocked' THEN 'type_mismatch'
        WHEN x.pilot_state_type = 'Unknown' THEN 'unknown'
        ELSE 'review'
    END AS type_alignment
FROM mes_custom.state_xref x
JOIN mes_core.state_definition sd ON x.mes_state_id = sd.state_id
JOIN mes_core.state_type st ON sd.state_type_id = st.state_type_id
ORDER BY x.pilot_state_code;

COMMENT ON VIEW mes_custom.v_state_complete IS 'Complete state mapping with type alignment check';

-- ----------------------------------------------------------------------------
-- Function: get_mes_state_id - Translate Pilot state code to MES state ID
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_custom.get_mes_state_id(p_pilot_state_code INT)
RETURNS BIGINT AS $$
    SELECT mes_state_id
    FROM mes_custom.state_xref
    WHERE pilot_state_code = p_pilot_state_code;
$$ LANGUAGE SQL STABLE;

COMMENT ON FUNCTION mes_custom.get_mes_state_id IS 'Translates a Pilot state code to the corresponding MES Core state ID';

-- ----------------------------------------------------------------------------
-- Function: get_pilot_state_code - Translate MES state ID to Pilot code
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_custom.get_pilot_state_code(p_mes_state_id BIGINT)
RETURNS INT AS $$
    SELECT pilot_state_code
    FROM mes_custom.state_xref
    WHERE mes_state_id = p_mes_state_id;
$$ LANGUAGE SQL STABLE;

COMMENT ON FUNCTION mes_custom.get_pilot_state_code IS 'Translates an MES Core state ID to the corresponding Pilot state code';

-- Index for reverse lookups
CREATE INDEX IF NOT EXISTS idx_state_xref_mes_state_id ON mes_custom.state_xref(mes_state_id);


-- ============================================================================
-- SECTION 2: ITEM/PRODUCT RECONCILIATION
-- Purpose: Bridge Pilot/UNS item IDs to MES Core product IDs
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: item_xref - Core ID Mapping
-- Maps Pilot item IDs to MES Core product IDs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mes_custom.item_xref (
    pilot_item_id      BIGINT PRIMARY KEY,
    pilot_item_name    VARCHAR(100) NOT NULL,
    mes_product_id     BIGINT REFERENCES mes_core.product_definition(product_id),
    created_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE mes_custom.item_xref IS 'Cross-reference linking Pilot item IDs to MES Core product IDs';
COMMENT ON COLUMN mes_custom.item_xref.pilot_item_id IS 'Primary key from Pilot/UNS system';
COMMENT ON COLUMN mes_custom.item_xref.mes_product_id IS 'Foreign key to mes_core.product_definition (NULL if not yet in MES)';

-- ----------------------------------------------------------------------------
-- Table: item_extended_attributes - Schema Gap Filler
-- Stores Pilot-specific attributes not present in MES Core
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mes_custom.item_extended_attributes (
    pilot_item_id      BIGINT PRIMARY KEY REFERENCES mes_custom.item_xref(pilot_item_id),
    parent_item_id     BIGINT REFERENCES mes_custom.item_xref(pilot_item_id),
    item_class         VARCHAR(20),
    bottle_size        VARCHAR(20),
    label_variant      VARCHAR(50),
    pack_count         INT,

    CONSTRAINT chk_item_class CHECK (item_class IN ('Mix', 'Bottle', 'Pack'))
);

COMMENT ON TABLE mes_custom.item_extended_attributes IS 'Extended attributes from Pilot not available in MES Core';
COMMENT ON COLUMN mes_custom.item_extended_attributes.parent_item_id IS 'BOM hierarchy - references parent item for Pack->Bottle->Mix relationship';
COMMENT ON COLUMN mes_custom.item_extended_attributes.item_class IS 'Product classification: Mix (raw), Bottle (filled), Pack (packaged)';

-- ----------------------------------------------------------------------------
-- Initial Data: item_xref (22 Pilot items with MES mappings)
-- Uses name-based lookups to find product_id values dynamically
-- Note: "Standard" label variants map to base MES products
-- ----------------------------------------------------------------------------
INSERT INTO mes_custom.item_xref (pilot_item_id, pilot_item_name, mes_product_id)
SELECT
    v.pilot_item_id,
    v.pilot_item_name,
    pd.product_id  -- Will be NULL if no match (LEFT JOIN)
FROM (VALUES
    -- Mix products (mapped to MES)
    (1::BIGINT,  'Orange Soda Mix',           'Orange Soda Mix'),
    (2,          'Cola Mix',                  'Cola Mix'),
    -- Bottle products (mapped to MES)
    (3,          'Orange Soda 0.5L',          'Orange Soda 0.5L'),
    (4,          'Cola Soda 0.5L',            'Cola Soda 0.5L'),
    -- Orange Pack products
    (5,          'Orange 0.5L 4Pk',           NULL),  -- Not in MES
    (6,          'Orange 0.5L 6Pk',           'Orange 0.5L 6Pk'),
    (7,          'Orange 0.5L 12Pk',          'Orange 0.5L 12Pk'),
    (8,          'Orange 0.5L 16Pk',          'Orange 0.5L 16Pk'),
    (9,          'Orange 0.5L 20Pk',          NULL),  -- Not in MES
    (10,         'Orange 0.5L 24Pk',          'Orange 0.5L 24Pk'),
    -- Cola Standard Pack products (map to base Cola products in MES)
    (11,         'Cola 0.5L 4Pk Standard',    NULL),  -- Not in MES
    (12,         'Cola 0.5L 6Pk Standard',    'Cola 0.5L 6Pk'),
    (13,         'Cola 0.5L 12Pk Standard',   'Cola 0.5L 12Pk'),
    (14,         'Cola 0.5L 16Pk Standard',   'Cola 0.5L 16Pk'),
    (15,         'Cola 0.5L 20Pk Standard',   NULL),  -- Not in MES
    (16,         'Cola 0.5L 24Pk Standard',   'Cola 0.5L 24Pk'),
    -- Cola Seasonal Pack products (not mapped - seasonal variants)
    (17,         'Cola 0.5L 4Pk Seasonal',    NULL),
    (18,         'Cola 0.5L 6Pk Seasonal',    NULL),
    (19,         'Cola 0.5L 12Pk Seasonal',   NULL),
    (20,         'Cola 0.5L 16Pk Seasonal',   NULL),
    (21,         'Cola 0.5L 20Pk Seasonal',   NULL),
    (22,         'Cola 0.5L 24Pk Seasonal',   NULL)
) AS v(pilot_item_id, pilot_item_name, mes_product_name)
LEFT JOIN mes_core.product_definition pd ON pd.product_name = v.mes_product_name
ON CONFLICT (pilot_item_id) DO UPDATE SET
    pilot_item_name = EXCLUDED.pilot_item_name,
    mes_product_id = EXCLUDED.mes_product_id,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Initial Data: item_extended_attributes (BOM hierarchy + attributes)
-- ----------------------------------------------------------------------------
INSERT INTO mes_custom.item_extended_attributes
    (pilot_item_id, parent_item_id, item_class, bottle_size, label_variant, pack_count)
VALUES
    -- Mix products (no parent, no packaging attributes)
    (1,  NULL, 'Mix',    NULL,   NULL,       NULL),
    (2,  NULL, 'Mix',    NULL,   NULL,       NULL),
    -- Bottle products (parent = mix)
    (3,  1,    'Bottle', '0.5L', NULL,       NULL),
    (4,  2,    'Bottle', '0.5L', NULL,       NULL),
    -- Orange Packs (parent = Orange bottle)
    (5,  3,    'Pack',   '0.5L', NULL,       4),
    (6,  3,    'Pack',   '0.5L', NULL,       6),
    (7,  3,    'Pack',   '0.5L', NULL,       12),
    (8,  3,    'Pack',   '0.5L', NULL,       16),
    (9,  3,    'Pack',   '0.5L', NULL,       20),
    (10, 3,    'Pack',   '0.5L', NULL,       24),
    -- Cola Standard Packs (parent = Cola bottle)
    (11, 4,    'Pack',   '0.5L', 'Standard', 4),
    (12, 4,    'Pack',   '0.5L', 'Standard', 6),
    (13, 4,    'Pack',   '0.5L', 'Standard', 12),
    (14, 4,    'Pack',   '0.5L', 'Standard', 16),
    (15, 4,    'Pack',   '0.5L', 'Standard', 20),
    (16, 4,    'Pack',   '0.5L', 'Standard', 24),
    -- Cola Seasonal Packs (parent = Cola bottle)
    (17, 4,    'Pack',   '0.5L', 'Seasonal', 4),
    (18, 4,    'Pack',   '0.5L', 'Seasonal', 6),
    (19, 4,    'Pack',   '0.5L', 'Seasonal', 12),
    (20, 4,    'Pack',   '0.5L', 'Seasonal', 16),
    (21, 4,    'Pack',   '0.5L', 'Seasonal', 20),
    (22, 4,    'Pack',   '0.5L', 'Seasonal', 24)
ON CONFLICT (pilot_item_id) DO UPDATE SET
    parent_item_id = EXCLUDED.parent_item_id,
    item_class = EXCLUDED.item_class,
    bottle_size = EXCLUDED.bottle_size,
    label_variant = EXCLUDED.label_variant,
    pack_count = EXCLUDED.pack_count;

-- ----------------------------------------------------------------------------
-- View: v_item_complete - Full item mapping with all attributes
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mes_custom.v_item_complete AS
SELECT
    x.pilot_item_id,
    x.pilot_item_name,
    x.mes_product_id,
    p.product_name AS mes_product_name,
    CASE WHEN x.mes_product_id IS NULL THEN 'missing' ELSE 'mapped' END AS mapping_status,
    e.parent_item_id,
    parent_x.pilot_item_name AS parent_item_name,
    e.item_class,
    e.bottle_size,
    e.label_variant,
    e.pack_count,
    p.unit_of_measure,
    p.ideal_cycle_time AS ideal_cycle_time_seconds
FROM mes_custom.item_xref x
LEFT JOIN mes_core.product_definition p ON x.mes_product_id = p.product_id
LEFT JOIN mes_custom.item_extended_attributes e ON x.pilot_item_id = e.pilot_item_id
LEFT JOIN mes_custom.item_xref parent_x ON e.parent_item_id = parent_x.pilot_item_id;

COMMENT ON VIEW mes_custom.v_item_complete IS 'Complete item view joining Pilot, MES Core, and extended attributes';

-- ----------------------------------------------------------------------------
-- View: v_items_missing_in_mes - Items needing MES Core configuration
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mes_custom.v_items_missing_in_mes AS
SELECT
    x.pilot_item_id,
    x.pilot_item_name,
    e.item_class,
    e.pack_count,
    e.label_variant
FROM mes_custom.item_xref x
JOIN mes_custom.item_extended_attributes e ON x.pilot_item_id = e.pilot_item_id
WHERE x.mes_product_id IS NULL;

COMMENT ON VIEW mes_custom.v_items_missing_in_mes IS 'Items defined in Pilot but not yet configured in MES Core';

-- ----------------------------------------------------------------------------
-- View: v_item_bom_hierarchy - Recursive BOM structure
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mes_custom.v_item_bom_hierarchy AS
WITH RECURSIVE bom AS (
    SELECT
        e.pilot_item_id,
        x.pilot_item_name,
        e.item_class,
        e.parent_item_id,
        1 AS level,
        x.pilot_item_name::TEXT AS path
    FROM mes_custom.item_extended_attributes e
    JOIN mes_custom.item_xref x ON e.pilot_item_id = x.pilot_item_id
    WHERE e.parent_item_id IS NULL

    UNION ALL

    SELECT
        e.pilot_item_id,
        x.pilot_item_name,
        e.item_class,
        e.parent_item_id,
        bom.level + 1,
        bom.path || ' > ' || x.pilot_item_name
    FROM mes_custom.item_extended_attributes e
    JOIN mes_custom.item_xref x ON e.pilot_item_id = x.pilot_item_id
    JOIN bom ON e.parent_item_id = bom.pilot_item_id
)
SELECT * FROM bom ORDER BY path;

COMMENT ON VIEW mes_custom.v_item_bom_hierarchy IS 'Recursive view showing full BOM hierarchy with path';

-- ----------------------------------------------------------------------------
-- Function: get_mes_product_id - Translate Pilot ID to MES ID
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_custom.get_mes_product_id(p_pilot_item_id BIGINT)
RETURNS BIGINT AS $$
    SELECT mes_product_id
    FROM mes_custom.item_xref
    WHERE pilot_item_id = p_pilot_item_id;
$$ LANGUAGE SQL STABLE;

COMMENT ON FUNCTION mes_custom.get_mes_product_id IS 'Translates a Pilot item ID to the corresponding MES Core product ID';

-- ----------------------------------------------------------------------------
-- Function: get_pilot_item_id - Translate MES ID to Pilot ID
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_custom.get_pilot_item_id(p_mes_product_id BIGINT)
RETURNS BIGINT AS $$
    SELECT pilot_item_id
    FROM mes_custom.item_xref
    WHERE mes_product_id = p_mes_product_id;
$$ LANGUAGE SQL STABLE;

COMMENT ON FUNCTION mes_custom.get_pilot_item_id IS 'Translates an MES Core product ID to the corresponding Pilot item ID';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_item_xref_mes_product_id ON mes_custom.item_xref(mes_product_id);
CREATE INDEX IF NOT EXISTS idx_item_extended_parent ON mes_custom.item_extended_attributes(parent_item_id);
CREATE INDEX IF NOT EXISTS idx_item_extended_class ON mes_custom.item_extended_attributes(item_class);


-- ============================================================================
-- SECTION 3: LIQUID ATTRIBUTES
-- Purpose: Store physical properties (density, viscosity) for liquid items
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: item_liquid_attributes - Physical Properties for Liquid Products
-- Stores density and viscosity for Mix products and other liquid items
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mes_custom.item_liquid_attributes (
    pilot_item_id      BIGINT PRIMARY KEY REFERENCES mes_custom.item_xref(pilot_item_id),
    density            NUMERIC(10, 4),        -- kg/m³ (water = 1000)
    density_uom        VARCHAR(20) DEFAULT 'kg/m³',
    viscosity          NUMERIC(10, 4),        -- mPa·s (centiPoise, water ≈ 1.0)
    viscosity_uom      VARCHAR(20) DEFAULT 'mPa·s',
    temperature_ref    NUMERIC(5, 2) DEFAULT 20.0,  -- Reference temperature in °C
    notes              TEXT,
    created_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE mes_custom.item_liquid_attributes IS 'Physical properties (density, viscosity) for liquid items like Mix products';
COMMENT ON COLUMN mes_custom.item_liquid_attributes.pilot_item_id IS 'Foreign key to item_xref - links to Pilot item ID and thus MES product';
COMMENT ON COLUMN mes_custom.item_liquid_attributes.density IS 'Liquid density in kg/m³ (water at 20°C = 998.2)';
COMMENT ON COLUMN mes_custom.item_liquid_attributes.viscosity IS 'Dynamic viscosity in mPa·s (centiPoise). Water at 20°C ≈ 1.0';
COMMENT ON COLUMN mes_custom.item_liquid_attributes.temperature_ref IS 'Reference temperature for measurements in °C (default 20°C)';

-- ----------------------------------------------------------------------------
-- Initial Data: item_liquid_attributes (Mix products)
-- Industry-standard values for concentrated beverage syrups (~11-12% Brix)
-- ----------------------------------------------------------------------------
INSERT INTO mes_custom.item_liquid_attributes
    (pilot_item_id, density, density_uom, viscosity, viscosity_uom, temperature_ref, notes)
VALUES
    -- Orange Soda Mix (concentrated syrup, ~11% Brix sugar content)
    (1, 1092.0, 'kg/m³', 42.3, 'mPa·s', 20.0, 'Concentrated syrup. ~11% Brix. Specific gravity 1.092.'),
    -- Cola Mix (concentrated syrup, ~12% Brix, higher viscosity from caramel)
    (2, 1118.0, 'kg/m³', 58.5, 'mPa·s', 20.0, 'Concentrated syrup. ~12% Brix. Specific gravity 1.118. Caramel coloring increases viscosity.')
ON CONFLICT (pilot_item_id) DO UPDATE SET
    density = EXCLUDED.density,
    density_uom = EXCLUDED.density_uom,
    viscosity = EXCLUDED.viscosity,
    viscosity_uom = EXCLUDED.viscosity_uom,
    temperature_ref = EXCLUDED.temperature_ref,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- View: v_item_liquid_complete - Full liquid attributes with item details
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mes_custom.v_item_liquid_complete AS
SELECT
    x.pilot_item_id,
    x.pilot_item_name,
    x.mes_product_id,
    p.product_name AS mes_product_name,
    l.density,
    l.density_uom,
    l.viscosity,
    l.viscosity_uom,
    l.temperature_ref,
    l.notes,
    l.updated_at
FROM mes_custom.item_liquid_attributes l
JOIN mes_custom.item_xref x ON l.pilot_item_id = x.pilot_item_id
LEFT JOIN mes_core.product_definition p ON x.mes_product_id = p.product_id;

COMMENT ON VIEW mes_custom.v_item_liquid_complete IS 'Complete liquid attributes view with item and product details';

-- ----------------------------------------------------------------------------
-- Function: get_liquid_density - Get density for a Pilot item
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_custom.get_liquid_density(p_pilot_item_id BIGINT)
RETURNS NUMERIC AS $$
    SELECT density
    FROM mes_custom.item_liquid_attributes
    WHERE pilot_item_id = p_pilot_item_id;
$$ LANGUAGE SQL STABLE;

COMMENT ON FUNCTION mes_custom.get_liquid_density IS 'Returns density (kg/m³) for a given Pilot item ID';

-- ----------------------------------------------------------------------------
-- Function: get_liquid_viscosity - Get viscosity for a Pilot item
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_custom.get_liquid_viscosity(p_pilot_item_id BIGINT)
RETURNS NUMERIC AS $$
    SELECT viscosity
    FROM mes_custom.item_liquid_attributes
    WHERE pilot_item_id = p_pilot_item_id;
$$ LANGUAGE SQL STABLE;

COMMENT ON FUNCTION mes_custom.get_liquid_viscosity IS 'Returns viscosity (mPa·s) for a given Pilot item ID';


-- ============================================================================
-- VERSION TRACKING
-- ============================================================================
INSERT INTO mes_custom.custom_schema_version (version, description, applied_at)
VALUES ('1.2.0', 'Added item_liquid_attributes table for density and viscosity properties', CURRENT_TIMESTAMP);
