-- ============================================================================
-- 02. STATE TYPES (Machine State Categories)
-- Run Order: 2 of 10
-- ============================================================================

INSERT INTO mes_core.state_type (state_type_name, state_type_description, state_type_color, is_downtime, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Running', 'Actively executing a production or process step', '#2ECC71', false, 'seed', NOW(), 'seed', NOW(), false),
    ('PlannedDowntime', 'Scheduled stop (cleaning, CIP, changeover, planned maintenance)', '#3498DB', true, 'seed', NOW(), 'seed', NOW(), false),
    ('UnplannedDowntime', 'Faulted or unplanned stop', '#E74C3C', true, 'seed', NOW(), 'seed', NOW(), false),
    ('Idle', 'Not running, available or standby (no demand or waiting)', '#95A5A6', false, 'seed', NOW(), 'seed', NOW(), false),
    ('Blocked', 'Stopped due to downstream constraint or unable to discharge', '#E67E22', true, 'seed', NOW(), 'seed', NOW(), false)
ON CONFLICT (state_type_name) DO UPDATE SET
    state_type_description = EXCLUDED.state_type_description,
    state_type_color = EXCLUDED.state_type_color,
    is_downtime = EXCLUDED.is_downtime,
    updated_by = 'seed',
    updated_at = NOW(),
    removed = false;
