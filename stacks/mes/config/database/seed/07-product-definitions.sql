-- ============================================================================
-- 07. PRODUCT DEFINITIONS (SKUs)
-- Run Order: 7 of 10 (requires 06-product-families.sql)
--
-- Note: Uses conditional insert to be idempotent. Products are only inserted
-- if they don't already exist (checked by product_name).
-- ============================================================================

-- Insert products only if they don't already exist
INSERT INTO mes_core.product_definition (
    product_name, product_description, product_family_id,
    unit_of_measure, tolerance, ideal_cycle_time,
    created_by, created_at, updated_by, updated_at, removed
)
SELECT
    v.product_name,
    v.product_description,
    pf.product_family_id,
    v.unit_of_measure,
    v.tolerance,
    v.ideal_cycle_time,
    'seed', NOW(), 'seed', NOW(), false
FROM (VALUES
    -- ========================================================================
    -- Mix Products (raw materials batched in vats)
    -- ========================================================================
    ('Cola Mix',           'Base syrup/mix for Cola products',    'Mix',    'batch', NULL::numeric, NULL::numeric),
    ('Orange Soda Mix',    'Base syrup/mix for Orange products',  'Mix',    'batch', NULL, NULL),

    -- ========================================================================
    -- Bottle Products (single filled units)
    -- ========================================================================
    ('Cola Soda 0.5L',     '0.5L filled Cola bottle',             'Bottle', 'ea',    NULL, 2.5),
    ('Orange Soda 0.5L',   '0.5L filled Orange bottle',           'Bottle', 'ea',    NULL, 2.5),

    -- ========================================================================
    -- Pack Products - Cola Standard (secondary packaging)
    -- Note: "Standard" label variants from Pilot map to these base products.
    --       Label variant is tracked in mes_custom.item_extended_attributes
    -- ========================================================================
    ('Cola 0.5L 4Pk',      '4-pack of 0.5L Cola bottles',         'Pack',   'pack',  NULL, 10.0),
    ('Cola 0.5L 6Pk',      '6-pack of 0.5L Cola bottles',         'Pack',   'pack',  NULL, 15.0),
    ('Cola 0.5L 12Pk',     '12-pack of 0.5L Cola bottles',        'Pack',   'pack',  NULL, 25.0),
    ('Cola 0.5L 16Pk',     '16-pack of 0.5L Cola bottles',        'Pack',   'pack',  NULL, 32.0),
    ('Cola 0.5L 20Pk',     '20-pack of 0.5L Cola bottles',        'Pack',   'pack',  NULL, 40.0),
    ('Cola 0.5L 24Pk',     '24-pack of 0.5L Cola bottles',        'Pack',   'pack',  NULL, 45.0),

    -- ========================================================================
    -- Pack Products - Cola Seasonal (seasonal label variants)
    -- ========================================================================
    ('Cola 0.5L 4Pk Seasonal',   '4-pack of 0.5L Cola bottles (Seasonal)',   'Pack', 'pack', NULL, 10.0),
    ('Cola 0.5L 6Pk Seasonal',   '6-pack of 0.5L Cola bottles (Seasonal)',   'Pack', 'pack', NULL, 15.0),
    ('Cola 0.5L 12Pk Seasonal',  '12-pack of 0.5L Cola bottles (Seasonal)',  'Pack', 'pack', NULL, 25.0),
    ('Cola 0.5L 16Pk Seasonal',  '16-pack of 0.5L Cola bottles (Seasonal)',  'Pack', 'pack', NULL, 32.0),
    ('Cola 0.5L 20Pk Seasonal',  '20-pack of 0.5L Cola bottles (Seasonal)',  'Pack', 'pack', NULL, 40.0),
    ('Cola 0.5L 24Pk Seasonal',  '24-pack of 0.5L Cola bottles (Seasonal)',  'Pack', 'pack', NULL, 45.0),

    -- ========================================================================
    -- Pack Products - Orange (secondary packaging)
    -- ========================================================================
    ('Orange 0.5L 4Pk',    '4-pack of 0.5L Orange bottles',       'Pack',   'pack',  NULL, 10.0),
    ('Orange 0.5L 6Pk',    '6-pack of 0.5L Orange bottles',       'Pack',   'pack',  NULL, 15.0),
    ('Orange 0.5L 12Pk',   '12-pack of 0.5L Orange bottles',      'Pack',   'pack',  NULL, 25.0),
    ('Orange 0.5L 16Pk',   '16-pack of 0.5L Orange bottles',      'Pack',   'pack',  NULL, 32.0),
    ('Orange 0.5L 20Pk',   '20-pack of 0.5L Orange bottles',      'Pack',   'pack',  NULL, 40.0),
    ('Orange 0.5L 24Pk',   '24-pack of 0.5L Orange bottles',      'Pack',   'pack',  NULL, 45.0)
) AS v(product_name, product_description, family_name, unit_of_measure, tolerance, ideal_cycle_time)
JOIN mes_core.product_family pf ON pf.product_family_name = v.family_name
WHERE NOT EXISTS (
    SELECT 1 FROM mes_core.product_definition pd
    WHERE pd.product_name = v.product_name
);
