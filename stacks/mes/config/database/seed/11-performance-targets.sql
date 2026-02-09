-- ============================================================================
-- 11. PERFORMANCE TARGETS (Product × Asset Rate Targets)
-- Run Order: 11 (requires 07-product-definitions.sql, 10-asset-definitions.sql)
--
-- Defines expected throughput rates for specific product + asset combinations.
-- Target values are derived from ideal_cycle_time: 3600 / ideal_cycle_time.
--
-- Uses product_name + asset tag_path lookups since IDs are auto-generated.
-- ============================================================================

INSERT INTO mes_core.performance_target (
    product_id, asset_id, target_value, target_unit,
    created_by, created_at, updated_by, updated_at, removed
)
SELECT
    pd.product_id,
    ad.asset_id,
    v.target_value,
    'units/hour',
    'seed', NOW(), 'seed', NOW(), false
FROM (VALUES
    -- ========================================================================
    -- Bottle Products on Fillers (18947 units/hr = 3600/0.19)
    -- ========================================================================
    ('Cola Soda 0.5L',     'Cappy Hour Inc/Site 1/Filler Production/FillingLine01/Filler',  18947.00),
    ('Cola Soda 0.5L',     'Cappy Hour Inc/Site 1/Filler Production/FillingLine02/Filler',  18947.00),
    ('Cola Soda 0.5L',     'Cappy Hour Inc/Site 1/Filler Production/FillingLine03/Filler',  18947.00),
    ('Orange Soda 0.5L',   'Cappy Hour Inc/Site 1/Filler Production/FillingLine01/Filler',  18947.00),
    ('Orange Soda 0.5L',   'Cappy Hour Inc/Site 1/Filler Production/FillingLine03/Filler',  18947.00),

    -- ========================================================================
    -- 12Pk Products on Packaging Lines (15000 units/hr = 3600/0.24)
    -- ========================================================================
    -- Orange 12Pk → LabelerLine04
    ('Orange 0.5L 12Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Labeler',   15000.00),
    ('Orange 0.5L 12Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Packager',  15000.00),
    ('Orange 0.5L 12Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Sealer',    15000.00),
    -- Cola 12Pk → LabelerLine03
    ('Cola 0.5L 12Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Labeler',   15000.00),
    ('Cola 0.5L 12Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Packager',  15000.00),
    ('Cola 0.5L 12Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Sealer',    15000.00),

    -- ========================================================================
    -- 16Pk Products on Packaging Lines (17143 units/hr = 3600/0.21)
    -- ========================================================================
    -- Orange 16Pk → LabelerLine01
    ('Orange 0.5L 16Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Labeler',   17143.00),
    ('Orange 0.5L 16Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Packager',  17143.00),
    ('Orange 0.5L 16Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Sealer',    17143.00),
    -- Cola 16Pk → LabelerLine02 + LabelerLine04
    ('Cola 0.5L 16Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Labeler',   17143.00),
    ('Cola 0.5L 16Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Packager',  17143.00),
    ('Cola 0.5L 16Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Sealer',    17143.00),
    ('Cola 0.5L 16Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Labeler',   17143.00),
    ('Cola 0.5L 16Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Packager',  17143.00),
    ('Cola 0.5L 16Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Sealer',    17143.00),

    -- ========================================================================
    -- 20Pk Products on Packaging Lines (18947 units/hr = 3600/0.19)
    -- ========================================================================
    -- Orange 20Pk → LabelerLine01 + LabelerLine03
    ('Orange 0.5L 20Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Labeler',   18947.00),
    ('Orange 0.5L 20Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Packager',  18947.00),
    ('Orange 0.5L 20Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Sealer',    18947.00),
    ('Orange 0.5L 20Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Labeler',   18947.00),
    ('Orange 0.5L 20Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Packager',  18947.00),
    ('Orange 0.5L 20Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Sealer',    18947.00),
    -- Cola 20Pk → LabelerLine01 + LabelerLine02 + LabelerLine03
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Labeler',   18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Packager',  18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Sealer',    18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Labeler',   18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Packager',  18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Sealer',    18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Labeler',   18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Packager',  18947.00),
    ('Cola 0.5L 20Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Sealer',    18947.00),

    -- ========================================================================
    -- 24Pk Products on Packaging Lines (20000 units/hr = 3600/0.18)
    -- ========================================================================
    -- Cola 24Pk → LabelerLine03 + LabelerLine04
    ('Cola 0.5L 24Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Labeler',   20000.00),
    ('Cola 0.5L 24Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Packager',  20000.00),
    ('Cola 0.5L 24Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Sealer',    20000.00),
    ('Cola 0.5L 24Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Labeler',   20000.00),
    ('Cola 0.5L 24Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Packager',  20000.00),
    ('Cola 0.5L 24Pk',     'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Sealer',    20000.00),
    -- Orange 24Pk → LabelerLine03
    ('Orange 0.5L 24Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Labeler',   20000.00),
    ('Orange 0.5L 24Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Packager',  20000.00),
    ('Orange 0.5L 24Pk',   'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Sealer',    20000.00),

    -- ========================================================================
    -- 4Pk Products on Packaging Lines (12000 units/hr = 3600/0.30)
    -- ========================================================================
    -- Cola 4Pk → LabelerLine01 + LabelerLine02
    ('Cola 0.5L 4Pk',      'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Labeler',   12000.00),
    ('Cola 0.5L 4Pk',      'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Packager',  12000.00),
    ('Cola 0.5L 4Pk',      'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Sealer',    12000.00),
    ('Cola 0.5L 4Pk',      'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Labeler',   12000.00),
    ('Cola 0.5L 4Pk',      'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Packager',  12000.00),
    ('Cola 0.5L 4Pk',      'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Sealer',    12000.00)

) AS v(product_name, asset_tag_path, target_value)
JOIN mes_core.product_definition pd ON pd.product_name = v.product_name
JOIN mes_core.asset_definition ad ON ad.tag_path = v.asset_tag_path
WHERE NOT EXISTS (
    SELECT 1 FROM mes_core.performance_target pt
    WHERE pt.product_id = pd.product_id
      AND pt.asset_id = ad.asset_id
);
