-- ============================================================================
-- 08. STATE DEFINITIONS (Specific Machine States)
-- Run Order: 8 of 10 (requires 02-state-types.sql)
-- ============================================================================

INSERT INTO mes_core.state_definition (state_type_id, state_name, state_description, state_color, created_by, created_at, updated_by, updated_at, removed)
SELECT
    st.state_type_id,
    v.state_name,
    v.state_description,
    v.state_color,
    'seed', NOW(), 'seed', NOW(), false
FROM (VALUES
    -- Running States (Pilot codes 0-5)
    ('Running', 'Running',           'Generic running state when no sub-state is provided', '#2ECC71'),
    ('Running', 'Pasteurize',        'Pasteurization step active (where applicable)', '#2ECC71'),
    ('Running', 'Cool',              'Cooling step active (where applicable)', '#2ECC71'),
    ('Running', 'Fill',              'Filling and capping active', '#2ECC71'),
    ('Running', 'Mix',               'Mixing or batching active (vats)', '#2ECC71'),
    ('Running', 'Transfer',          'Transfer in progress (vat to tank, tank to filler feed)', '#2ECC71'),
    -- Unknown/Unmapped
    ('UnplannedDowntime', 'Unknown', 'Used only for data-quality handling when source reports UNKNOWN', '#E74C3C'),
    -- Unplanned Downtime (Pilot code 100)
    ('UnplannedDowntime', 'Unplanned Downtime', 'Faulted or unplanned stop event', '#E74C3C'),
    -- Idle (Pilot code 200)
    ('Idle', 'Idle',                 'Asset is stopped but available', '#95A5A6'),
    -- Blocked (Pilot code 202)
    ('Blocked', 'Blocked',           'Asset prevented from running due to downstream stop or backpressure', '#E67E22'),
    -- Planned Downtime (Pilot codes 300-306)
    ('PlannedDowntime', 'Planned Downtime', 'Generic planned stop', '#3498DB'),
    ('PlannedDowntime', 'Changeover',       'Product or format changeover', '#3498DB'),
    ('PlannedDowntime', 'CIP',              'Clean-in-place cycle', '#3498DB'),
    ('PlannedDowntime', 'Cleaning',         'Non-CIP cleaning or sanitation', '#3498DB')
) AS v(state_type_name, state_name, state_description, state_color)
JOIN mes_core.state_type st ON st.state_type_name = v.state_type_name
ON CONFLICT (state_name) DO UPDATE SET
    state_type_id = EXCLUDED.state_type_id,
    state_description = EXCLUDED.state_description,
    state_color = EXCLUDED.state_color,
    updated_by = 'seed',
    updated_at = NOW(),
    removed = false;
