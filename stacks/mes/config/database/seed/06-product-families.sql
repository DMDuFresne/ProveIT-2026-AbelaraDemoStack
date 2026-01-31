-- ============================================================================
-- 06. PRODUCT FAMILIES (Product Categories)
-- Run Order: 6 of 10
-- ============================================================================

INSERT INTO mes_core.product_family (product_family_name, product_family_description, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Mix', 'Syrup/mix used for production (batched in vats)', 'seed', NOW(), 'seed', NOW(), false),
    ('Bottle', 'Finished bottled product (single unit)', 'seed', NOW(), 'seed', NOW(), false),
    ('Pack', 'Secondary packaging configuration (6pk / 16pk / 24pk)', 'seed', NOW(), 'seed', NOW(), false),
    ('Pallet', 'Optional: pallet becomes a managed unit of measure for finished goods reporting', 'seed', NOW(), 'seed', NOW(), false)
ON CONFLICT (product_family_name) DO UPDATE SET
    product_family_description = EXCLUDED.product_family_description,
    updated_by = 'seed',
    updated_at = NOW(),
    removed = false;
