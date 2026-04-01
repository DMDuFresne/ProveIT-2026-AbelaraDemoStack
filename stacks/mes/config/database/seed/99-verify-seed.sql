-- ============================================================================
-- VERIFICATION QUERIES
-- Run after all seed scripts to verify data was loaded correctly
-- ============================================================================

-- ============================================================================
-- MES CORE TABLE COUNTS
-- ============================================================================
SELECT 'asset_type' as table_name, COUNT(*) as count FROM mes_core.asset_type WHERE removed = false
UNION ALL SELECT 'state_type', COUNT(*) FROM mes_core.state_type WHERE removed = false
UNION ALL SELECT 'count_type', COUNT(*) FROM mes_core.count_type WHERE removed = false
UNION ALL SELECT 'measurement_type', COUNT(*) FROM mes_core.measurement_type WHERE removed = false
UNION ALL SELECT 'downtime_reason', COUNT(*) FROM mes_core.downtime_reason WHERE removed = false
UNION ALL SELECT 'product_family', COUNT(*) FROM mes_core.product_family WHERE removed = false
UNION ALL SELECT 'product_definition', COUNT(*) FROM mes_core.product_definition WHERE removed = false
UNION ALL SELECT 'state_definition', COUNT(*) FROM mes_core.state_definition WHERE removed = false
UNION ALL SELECT 'kpi_definition', COUNT(*) FROM mes_core.kpi_definition WHERE removed = false
UNION ALL SELECT 'asset_definition', COUNT(*) FROM mes_core.asset_definition WHERE removed = false
UNION ALL SELECT 'performance_target', COUNT(*) FROM mes_core.performance_target WHERE removed = false
ORDER BY table_name;

-- Expected MES Core counts:
-- asset_definition: 121  (66 Site 1 + 36 Site 2 + 19 Site 3)
-- asset_type: 18
-- count_type: 5
-- downtime_reason: 8
-- kpi_definition: 10
-- measurement_type: 9     (FlowRate removed — was duplicate of Flow)
-- performance_target: 50
-- product_definition: 23  (22 products + 1 Unknown sentinel)
-- product_family: 5       (4 families + 1 Unknown sentinel)
-- state_definition: 14
-- state_type: 5

-- ============================================================================
-- MES CUSTOM TABLE COUNTS (Pilot/UNS Reconciliation)
-- ============================================================================
SELECT 'state_xref (Pilot states)' as table_name, COUNT(*) as count FROM mes_custom.state_xref
UNION ALL SELECT 'item_xref (Pilot items)', COUNT(*) FROM mes_custom.item_xref
UNION ALL SELECT 'item_extended_attributes', COUNT(*) FROM mes_custom.item_extended_attributes
UNION ALL SELECT 'item_liquid_attributes', COUNT(*) FROM mes_custom.item_liquid_attributes
ORDER BY table_name;

-- Expected MES Custom counts:
-- item_extended_attributes: 22
-- item_liquid_attributes: 2
-- item_xref (Pilot items): 22
-- state_xref (Pilot states): 13

-- ============================================================================
-- MAPPING STATUS SUMMARY
-- ============================================================================
-- Items mapped vs missing in MES Core
SELECT
    CASE WHEN mes_product_id IS NULL THEN 'missing' ELSE 'mapped' END AS status,
    COUNT(*) as count
FROM mes_custom.item_xref
GROUP BY CASE WHEN mes_product_id IS NULL THEN 'missing' ELSE 'mapped' END;

-- Expected: mapped=22, missing=0

-- ============================================================================
-- PRODUCT TOLERANCE CHECK (demo polish)
-- ============================================================================
SELECT
    CASE
        WHEN tolerance IS NULL THEN 'NULL (needs fix)'
        WHEN tolerance = 0 THEN 'zero (sentinel)'
        ELSE 'set (' || tolerance || '%)'
    END AS tolerance_status,
    COUNT(*) as count
FROM mes_core.product_definition
WHERE removed = false
GROUP BY 1
ORDER BY 1;

-- Expected: no NULL tolerances
-- zero (sentinel): 1  (Unknown product)
-- set (1.5%): 2       (Bottle products)
-- set (2.0%): 18      (Pack products)
-- set (2.5%): 2       (Mix products)
