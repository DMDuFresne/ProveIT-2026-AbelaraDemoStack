-- ============================================================================
-- 21. CUSTOM ITEM CROSS-REFERENCE (Pilot Item IDs → MES Product IDs)
-- Run Order: 21 of 25 (requires 07-product-definitions.sql AND 999-custom-schema.sql)
--
-- Purpose: Maps Pilot/UNS item IDs to MES Core product IDs
-- Source:  Item-Reconciliation-Matrix.md (2026-01-24)
-- ============================================================================

-- ============================================================================
-- TABLE: item_xref - Core ID Mapping
-- Maps all 22 Pilot items to MES Core products (NULL if not in MES)
-- ============================================================================

INSERT INTO mes_custom.item_xref (pilot_item_id, pilot_item_name, mes_product_id)
SELECT
    v.pilot_item_id,
    v.pilot_item_name,
    pd.product_id  -- Will be NULL if no match (LEFT JOIN)
FROM (VALUES
    -- ========================================================================
    -- Mix Products (mapped to MES)
    -- ========================================================================
    (1::BIGINT,  'Orange Soda Mix',           'Orange Soda Mix'),
    (2,          'Cola Mix',                  'Cola Mix'),

    -- ========================================================================
    -- Bottle Products (mapped to MES)
    -- ========================================================================
    (3,          'Orange Soda 0.5L',          'Orange Soda 0.5L'),
    (4,          'Cola Soda 0.5L',            'Cola Soda 0.5L'),

    -- ========================================================================
    -- Orange Pack Products (all mapped to MES Core)
    -- ========================================================================
    (5,          'Orange 0.5L 4Pk',           'Orange 0.5L 4Pk'),
    (6,          'Orange 0.5L 6Pk',           'Orange 0.5L 6Pk'),
    (7,          'Orange 0.5L 12Pk',          'Orange 0.5L 12Pk'),
    (8,          'Orange 0.5L 16Pk',          'Orange 0.5L 16Pk'),
    (9,          'Orange 0.5L 20Pk',          'Orange 0.5L 20Pk'),
    (10,         'Orange 0.5L 24Pk',          'Orange 0.5L 24Pk'),

    -- ========================================================================
    -- Cola Standard Pack Products
    -- "Standard" label variants map to base Cola products in MES
    -- ========================================================================
    (11,         'Cola 0.5L 4Pk Standard',    'Cola 0.5L 4Pk'),
    (12,         'Cola 0.5L 6Pk Standard',    'Cola 0.5L 6Pk'),
    (13,         'Cola 0.5L 12Pk Standard',   'Cola 0.5L 12Pk'),
    (14,         'Cola 0.5L 16Pk Standard',   'Cola 0.5L 16Pk'),
    (15,         'Cola 0.5L 20Pk Standard',   'Cola 0.5L 20Pk'),
    (16,         'Cola 0.5L 24Pk Standard',   'Cola 0.5L 24Pk'),

    -- ========================================================================
    -- Cola Seasonal Pack Products (mapped to MES Seasonal products)
    -- ========================================================================
    (17,         'Cola 0.5L 4Pk Seasonal',    'Cola 0.5L 4Pk Seasonal'),
    (18,         'Cola 0.5L 6Pk Seasonal',    'Cola 0.5L 6Pk Seasonal'),
    (19,         'Cola 0.5L 12Pk Seasonal',   'Cola 0.5L 12Pk Seasonal'),
    (20,         'Cola 0.5L 16Pk Seasonal',   'Cola 0.5L 16Pk Seasonal'),
    (21,         'Cola 0.5L 20Pk Seasonal',   'Cola 0.5L 20Pk Seasonal'),
    (22,         'Cola 0.5L 24Pk Seasonal',   'Cola 0.5L 24Pk Seasonal')

) AS v(pilot_item_id, pilot_item_name, mes_product_name)
LEFT JOIN mes_core.product_definition pd ON pd.product_name = v.mes_product_name
ON CONFLICT (pilot_item_id) DO UPDATE SET
    pilot_item_name = EXCLUDED.pilot_item_name,
    mes_product_id = EXCLUDED.mes_product_id,
    updated_at = CURRENT_TIMESTAMP;


-- ============================================================================
-- TABLE: item_extended_attributes - BOM Hierarchy + Schema Gap Filler
-- Stores Pilot-specific attributes not present in MES Core
-- ============================================================================

INSERT INTO mes_custom.item_extended_attributes
    (pilot_item_id, parent_item_id, item_class, bottle_size, label_variant, pack_count)
VALUES
    -- ========================================================================
    -- Mix Products (BOM Level 0 - no parent)
    -- ========================================================================
    (1,  NULL, 'Mix',    NULL,   NULL,       NULL),
    (2,  NULL, 'Mix',    NULL,   NULL,       NULL),

    -- ========================================================================
    -- Bottle Products (BOM Level 1 - parent = Mix)
    -- ========================================================================
    (3,  1,    'Bottle', '0.5L', NULL,       NULL),  -- Orange bottle → Orange Mix
    (4,  2,    'Bottle', '0.5L', NULL,       NULL),  -- Cola bottle → Cola Mix

    -- ========================================================================
    -- Orange Packs (BOM Level 2 - parent = Orange Bottle)
    -- ========================================================================
    (5,  3,    'Pack',   '0.5L', NULL,       4),
    (6,  3,    'Pack',   '0.5L', NULL,       6),
    (7,  3,    'Pack',   '0.5L', NULL,       12),
    (8,  3,    'Pack',   '0.5L', NULL,       16),
    (9,  3,    'Pack',   '0.5L', NULL,       20),
    (10, 3,    'Pack',   '0.5L', NULL,       24),

    -- ========================================================================
    -- Cola Standard Packs (BOM Level 2 - parent = Cola Bottle)
    -- ========================================================================
    (11, 4,    'Pack',   '0.5L', 'Standard', 4),
    (12, 4,    'Pack',   '0.5L', 'Standard', 6),
    (13, 4,    'Pack',   '0.5L', 'Standard', 12),
    (14, 4,    'Pack',   '0.5L', 'Standard', 16),
    (15, 4,    'Pack',   '0.5L', 'Standard', 20),
    (16, 4,    'Pack',   '0.5L', 'Standard', 24),

    -- ========================================================================
    -- Cola Seasonal Packs (BOM Level 2 - parent = Cola Bottle)
    -- ========================================================================
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
