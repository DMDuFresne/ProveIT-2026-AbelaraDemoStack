-- ============================================================================
-- 00. RESERVED DATA (System Defaults)
-- Run Order: 0 (MUST run before all other seed files)
-- ============================================================================
-- This file creates reserved/system records with explicit IDs.
-- These are used as fallbacks when edge data is incomplete.
--
-- IMPORTANT: "Unknown" products are for EXCEPTION HANDLING, not normal
-- operations. High usage of Unknown products indicates a data quality
-- problem at the edge that should be investigated and fixed.
-- ============================================================================

-- ============================================================================
-- UNKNOWN PRODUCT FAMILY (Reserved ID = 1)
-- ============================================================================

INSERT INTO mes_core.product_family (
    product_family_id,
    product_family_name,
    product_family_description,
    created_by,
    created_at,
    updated_by,
    updated_at,
    removed
)
OVERRIDING SYSTEM VALUE
VALUES (
    1,
    'Unknown',
    'Reserved: Used when product information is not available from the edge. High usage indicates data quality issues requiring investigation.',
    'system',
    NOW(),
    'system',
    NOW(),
    false
)
ON CONFLICT (product_family_id) DO UPDATE SET
    product_family_name = EXCLUDED.product_family_name,
    product_family_description = EXCLUDED.product_family_description,
    updated_by = 'system',
    updated_at = NOW(),
    removed = false;

-- Ensure sequence starts after reserved IDs
SELECT setval('mes_core.product_family_product_family_id_seq', GREATEST(1, (SELECT MAX(product_family_id) FROM mes_core.product_family)));

-- ============================================================================
-- UNKNOWN PRODUCT (Reserved ID = 1)
-- ============================================================================

INSERT INTO mes_core.product_definition (
    product_id,
    product_name,
    product_description,
    product_family_id,
    unit_of_measure,
    tolerance,
    ideal_cycle_time,
    created_by,
    created_at,
    updated_by,
    updated_at,
    removed
)
OVERRIDING SYSTEM VALUE
VALUES (
    1,
    'Unknown',
    'Reserved: Used when product information is not available from the edge. Counts logged against this product indicate missing ProductId from equipment. Investigate edge data quality.',
    1,  -- References Unknown product family
    'ea',
    NULL,
    NULL,  -- No ideal cycle time - cannot calculate OEE Performance
    'system',
    NOW(),
    'system',
    NOW(),
    false
)
ON CONFLICT (product_id) DO UPDATE SET
    product_name = EXCLUDED.product_name,
    product_description = EXCLUDED.product_description,
    product_family_id = EXCLUDED.product_family_id,
    updated_by = 'system',
    updated_at = NOW(),
    removed = false;

-- Ensure sequence starts after reserved IDs
SELECT setval('mes_core.product_definition_product_id_seq', GREATEST(1, (SELECT MAX(product_id) FROM mes_core.product_definition)));

-- ============================================================================
-- Verification
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM mes_core.product_family WHERE product_family_id = 1 AND product_family_name = 'Unknown') THEN
        RAISE EXCEPTION 'SEED VERIFICATION FAILED: Unknown product family not created with ID=1';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM mes_core.product_definition WHERE product_id = 1 AND product_name = 'Unknown') THEN
        RAISE EXCEPTION 'SEED VERIFICATION FAILED: Unknown product not created with ID=1';
    END IF;

    RAISE NOTICE 'Reserved data verification passed: Unknown product family (ID=1) and Unknown product (ID=1) exist.';
END $$;
