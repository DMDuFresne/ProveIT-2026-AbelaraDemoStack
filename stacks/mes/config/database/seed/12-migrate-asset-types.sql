-- ============================================================================
-- 12. MIGRATE ASSET TYPES - Update generic types to specific types
-- Run Order: 12 (run on EXISTING databases to migrate from generic types)
--
-- This script migrates assets from generic "Work Center" and "Equipment" types
-- to specific types (Filler, Tank, Robot, etc.) to enable KPI script queries
-- like assets.getAssetsByType("Filler")
--
-- Safe to run multiple times - uses ON CONFLICT DO NOTHING for type inserts
-- and WHERE clauses that only match assets with generic types.
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Add new specific asset types (safe to re-run)
-- ============================================================================

-- Work Center replacements
INSERT INTO mes_core.asset_type (asset_type_name, asset_type_description, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Filler', 'Bottle/container filling equipment', 'migration', NOW(), 'migration', NOW(), false),
    ('CapLoader', 'Cap loading/capping equipment', 'migration', NOW(), 'migration', NOW(), false),
    ('Washer', 'Bottle/container washing equipment', 'migration', NOW(), 'migration', NOW(), false),
    ('Labeler', 'Label application equipment', 'migration', NOW(), 'migration', NOW(), false),
    ('Packager', 'Case/carton packing equipment', 'migration', NOW(), 'migration', NOW(), false),
    ('Sealer', 'Case sealing equipment', 'migration', NOW(), 'migration', NOW(), false)
ON CONFLICT (asset_type_name) DO NOTHING;

-- Equipment replacements
INSERT INTO mes_core.asset_type (asset_type_name, asset_type_description, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Tank', 'Storage tanks', 'migration', NOW(), 'migration', NOW(), false),
    ('Vat', 'Mixing vats', 'migration', NOW(), 'migration', NOW(), false),
    ('PalletStation', 'Pallet loading stations', 'migration', NOW(), 'migration', NOW(), false),
    ('Robot', 'Robotic palletizers', 'migration', NOW(), 'migration', NOW(), false),
    ('Wrapper', 'Stretch wrap equipment', 'migration', NOW(), 'migration', NOW(), false),
    ('Workstation', 'Manual work stations', 'migration', NOW(), 'migration', NOW(), false)
ON CONFLICT (asset_type_name) DO NOTHING;

-- ============================================================================
-- Step 2: Update Work Centers to specific types
-- ============================================================================

-- Fillers (asset_name = 'Filler')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Filler'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'Filler'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Work Center')
  AND removed IS DISTINCT FROM TRUE;

-- CapLoaders (asset_name = 'CapLoader')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'CapLoader'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'CapLoader'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Work Center')
  AND removed IS DISTINCT FROM TRUE;

-- Washers (asset_name = 'Washer')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Washer'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'Washer'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Work Center')
  AND removed IS DISTINCT FROM TRUE;

-- Labelers (asset_name = 'Labeler')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Labeler'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'Labeler'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Work Center')
  AND removed IS DISTINCT FROM TRUE;

-- Packagers (asset_name = 'Packager')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Packager'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'Packager'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Work Center')
  AND removed IS DISTINCT FROM TRUE;

-- Sealers (asset_name = 'Sealer')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Sealer'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'Sealer'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Work Center')
  AND removed IS DISTINCT FROM TRUE;

-- ============================================================================
-- Step 3: Update Equipment to specific types
-- ============================================================================

-- Tanks (asset_name LIKE 'Tank%')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Tank'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name LIKE 'Tank%'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Equipment')
  AND removed IS DISTINCT FROM TRUE;

-- Vats (asset_name LIKE 'Vat%')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Vat'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name LIKE 'Vat%'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Equipment')
  AND removed IS DISTINCT FROM TRUE;

-- PalletStations (asset_name LIKE 'Pallet%' - note: matches Pallet01, Pallet02, etc.)
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'PalletStation'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name LIKE 'Pallet%'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Equipment')
  AND removed IS DISTINCT FROM TRUE;

-- Robots (asset_name = 'Robot')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Robot'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'Robot'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Equipment')
  AND removed IS DISTINCT FROM TRUE;

-- Wrappers (asset_name = 'Wrapper')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Wrapper'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name = 'Wrapper'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Equipment')
  AND removed IS DISTINCT FROM TRUE;

-- Workstations (asset_name LIKE 'Workstation%')
UPDATE mes_core.asset_definition
SET
    asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Workstation'),
    updated_by = 'asset_type_migration',
    updated_at = NOW()
WHERE asset_name LIKE 'Workstation%'
  AND asset_type_id = (SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = 'Equipment')
  AND removed IS DISTINCT FROM TRUE;

COMMIT;

-- ============================================================================
-- Verification Query - Run this to verify the migration results
-- ============================================================================
SELECT
    at.asset_type_name,
    COUNT(*) as asset_count
FROM mes_core.asset_definition ad
JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
WHERE ad.removed IS DISTINCT FROM TRUE
GROUP BY at.asset_type_name
ORDER BY at.asset_type_name;

-- ============================================================================
-- Expected Results:
-- Asset Type      | Count
-- ----------------|-------
-- Area            | 4
-- CapLoader       | 3
-- Enterprise      | 1
-- Filler          | 3
-- Labeler         | 4
-- Line            | 16
-- Packager        | 4
-- PalletStation   | 4
-- Robot           | 2
-- Sealer          | 4
-- Site            | 3
-- Tank            | 6
-- Vat             | 4
-- Washer          | 3
-- Workstation     | 4
-- Wrapper         | 2
--
-- Note: "Work Center" and "Equipment" should show 0 assets after migration
-- ============================================================================
