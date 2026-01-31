-- ============================================================================
-- 03. COUNT TYPES (Production Counter Categories)
-- Run Order: 3 of 10
-- Note: No unique constraint on count_type_name - run on fresh database only
-- ============================================================================

INSERT INTO mes_core.count_type (count_type_name, count_type_description, count_type_unit, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('InfeedCount', 'Containers entering a process step (where measured)', 'ea', 'seed', NOW(), 'seed', NOW(), false),
    ('GoodCount', 'Accepted output count', 'ea', 'seed', NOW(), 'seed', NOW(), false),
    ('RejectCount', 'Rejected output count', 'ea', 'seed', NOW(), 'seed', NOW(), false),
    ('ScrapCount', 'Scrapped units (if tracked separately from rejects)', 'ea', 'seed', NOW(), 'seed', NOW(), false),
    ('PalletCount', 'Palletized finished units (where pallet count is available)', 'pallets', 'seed', NOW(), 'seed', NOW(), false);
