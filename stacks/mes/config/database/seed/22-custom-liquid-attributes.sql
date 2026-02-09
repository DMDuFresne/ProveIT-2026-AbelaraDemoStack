-- ============================================================================
-- 22. CUSTOM LIQUID ATTRIBUTES (Physical Properties for Mix Products)
-- Run Order: 22 of 25 (requires 21-custom-item-xref.sql)
--
-- Purpose: Stores density and viscosity for liquid items (syrups/mixes).
-- Used by analytics and process monitoring dashboards.
-- ============================================================================

INSERT INTO mes_custom.item_liquid_attributes
    (pilot_item_id, density, density_uom, viscosity, viscosity_uom, temperature_ref, notes)
VALUES
    -- Orange Soda Mix: ~11% Brix, specific gravity 1.092
    (1, 1092.0000, 'kg/m³', 42.3000, 'mPa·s', 20.00,
     'Concentrated syrup. ~11% Brix. Specific gravity 1.092.'),

    -- Cola Mix: ~12% Brix, specific gravity 1.118 (caramel coloring increases viscosity)
    (2, 1118.0000, 'kg/m³', 58.5000, 'mPa·s', 20.00,
     'Concentrated syrup. ~12% Brix. Specific gravity 1.118. Caramel coloring increases viscosity.')

ON CONFLICT (pilot_item_id) DO UPDATE SET
    density = EXCLUDED.density,
    density_uom = EXCLUDED.density_uom,
    viscosity = EXCLUDED.viscosity,
    viscosity_uom = EXCLUDED.viscosity_uom,
    temperature_ref = EXCLUDED.temperature_ref,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;
