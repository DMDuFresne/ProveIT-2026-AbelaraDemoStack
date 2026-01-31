-- ============================================================================
-- 05. DOWNTIME REASONS (Reason Code Catalog)
-- Run Order: 5 of 10
-- ============================================================================

INSERT INTO mes_core.downtime_reason (downtime_reason_code, downtime_reason_name, downtime_reason_description, is_planned, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('0', 'Not Assigned', 'No reason provided or not classified', false, 'seed', NOW(), 'seed', NOW(), false),
    ('14', 'Bottle Jam', 'Bottle jam condition', false, 'seed', NOW(), 'seed', NOW(), false),
    ('16', 'High Temperature', 'Temperature excursion causing stop', false, 'seed', NOW(), 'seed', NOW(), false),
    ('99', 'Other / Catch-All', 'Use when the reason does not match a defined catalog entry', false, 'seed', NOW(), 'seed', NOW(), false),
    ('100', 'Unplanned - General', 'Generic unplanned stop when a detailed reason is unavailable', false, 'seed', NOW(), 'seed', NOW(), false),
    ('301', 'Changeover', 'Changeover-related downtime', true, 'seed', NOW(), 'seed', NOW(), false),
    ('305', 'CIP', 'CIP-related downtime', true, 'seed', NOW(), 'seed', NOW(), false),
    ('306', 'Cleaning', 'Cleaning or sanitation downtime', true, 'seed', NOW(), 'seed', NOW(), false)
ON CONFLICT (downtime_reason_code) DO UPDATE SET
    downtime_reason_name = EXCLUDED.downtime_reason_name,
    downtime_reason_description = EXCLUDED.downtime_reason_description,
    is_planned = EXCLUDED.is_planned,
    updated_by = 'seed',
    updated_at = NOW(),
    removed = false;
