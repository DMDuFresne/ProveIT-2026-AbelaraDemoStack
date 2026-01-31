-- ============================================================================
-- 01. ASSET TYPES (ISA-95 Hierarchy + Specific Equipment Types)
-- Run Order: 1 of 10
-- ============================================================================

-- ISA-95 Hierarchy Types (structural)
INSERT INTO mes_core.asset_type (asset_type_name, asset_type_description, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Enterprise', 'Top-level company entity (Cappy Hour Inc.)', 'seed', NOW(), 'seed', NOW(), false),
    ('Site', 'A production plant (Site 1, Site 2, Site 3)', 'seed', NOW(), 'seed', NOW(), false),
    ('Area', 'Major functional grouping within a site (Liquid Processing, Filler Production, Packaging, Palletizing)', 'seed', NOW(), 'seed', NOW(), false),
    ('Line', 'A production line or logical line grouping within an area (e.g., FillingLine01, MixRoom01)', 'seed', NOW(), 'seed', NOW(), false),
    -- Legacy types (kept for backwards compatibility, prefer specific types below)
    ('Work Center', 'Sub-system within a line performing a distinct operation (e.g., Filler, Capper, Washer, Labeler, Packager, Robot Cell)', 'seed', NOW(), 'seed', NOW(), false),
    ('Equipment', 'Individual assets under a work center (e.g., Vat01–04, Tank01–06, Pallet Stations, Robots, Wrappers, Manual Workstations)', 'seed', NOW(), 'seed', NOW(), false)
ON CONFLICT (asset_type_name) DO UPDATE SET
    asset_type_description = EXCLUDED.asset_type_description,
    updated_by = 'seed',
    updated_at = NOW(),
    removed = false;

-- ============================================================================
-- Specific Work Center Types (replaces generic "Work Center")
-- These enable KPI scripts to query by specific equipment type
-- ============================================================================
INSERT INTO mes_core.asset_type (asset_type_name, asset_type_description, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Filler', 'Bottle/container filling equipment', 'seed', NOW(), 'seed', NOW(), false),
    ('CapLoader', 'Cap loading/capping equipment', 'seed', NOW(), 'seed', NOW(), false),
    ('Washer', 'Bottle/container washing equipment', 'seed', NOW(), 'seed', NOW(), false),
    ('Labeler', 'Label application equipment', 'seed', NOW(), 'seed', NOW(), false),
    ('Packager', 'Case/carton packing equipment', 'seed', NOW(), 'seed', NOW(), false),
    ('Sealer', 'Case sealing equipment', 'seed', NOW(), 'seed', NOW(), false)
ON CONFLICT (asset_type_name) DO UPDATE SET
    asset_type_description = EXCLUDED.asset_type_description,
    updated_by = 'seed',
    updated_at = NOW(),
    removed = false;

-- ============================================================================
-- Specific Equipment Types (replaces generic "Equipment")
-- These enable KPI scripts to query by specific equipment type
-- ============================================================================
INSERT INTO mes_core.asset_type (asset_type_name, asset_type_description, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Tank', 'Storage tanks', 'seed', NOW(), 'seed', NOW(), false),
    ('Vat', 'Mixing vats', 'seed', NOW(), 'seed', NOW(), false),
    ('PalletStation', 'Pallet loading stations', 'seed', NOW(), 'seed', NOW(), false),
    ('Robot', 'Robotic palletizers', 'seed', NOW(), 'seed', NOW(), false),
    ('Wrapper', 'Stretch wrap equipment', 'seed', NOW(), 'seed', NOW(), false),
    ('Workstation', 'Manual work stations', 'seed', NOW(), 'seed', NOW(), false)
ON CONFLICT (asset_type_name) DO UPDATE SET
    asset_type_description = EXCLUDED.asset_type_description,
    updated_by = 'seed',
    updated_at = NOW(),
    removed = false;
