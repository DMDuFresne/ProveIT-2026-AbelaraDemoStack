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
ORDER BY table_name;

-- Expected MES Core counts:
-- asset_type: 6
-- state_type: 5
-- count_type: 5
-- measurement_type: 8
-- downtime_reason: 8
-- product_family: 4
-- product_definition: 22
-- state_definition: 14
-- kpi_definition: 10
-- asset_definition: 67

-- ============================================================================
-- MES CUSTOM TABLE COUNTS (Pilot/UNS Reconciliation)
-- ============================================================================
SELECT 'state_xref (Pilot states)' as table_name, COUNT(*) as count FROM mes_custom.state_xref
UNION ALL SELECT 'item_xref (Pilot items)', COUNT(*) FROM mes_custom.item_xref
UNION ALL SELECT 'item_extended_attributes', COUNT(*) FROM mes_custom.item_extended_attributes
ORDER BY table_name;

-- Expected MES Custom counts:
-- state_xref (Pilot states): 14
-- item_xref (Pilot items): 22
-- item_extended_attributes: 22

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
