-- ============================================================================
-- 20. CUSTOM STATE CROSS-REFERENCE (Pilot State Codes → MES State IDs)
-- Run Order: 20 of 25 (requires 08-state-definitions.sql AND 999-custom-schema.sql)
--
-- Purpose: Maps Pilot/UNS state codes to MES Core state IDs
-- Source:  State-Reconciliation-Matrix.md (2026-01-24)
-- ============================================================================

-- Insert state cross-references using name-based lookups
INSERT INTO mes_custom.state_xref
    (pilot_state_code, pilot_state_name, pilot_state_type, mes_state_id, notes)
SELECT
    v.pilot_state_code,
    v.pilot_state_name,
    v.pilot_state_type,
    sd.state_id,
    v.notes
FROM (VALUES
    -- ========================================================================
    -- Running states (Pilot codes 0-5)
    -- These represent active production sub-states
    -- ========================================================================
    (0,   'Running',            'Running',           'Running',            NULL::TEXT),
    (1,   'Pasteurize',         'Running',           'Pasteurize',         NULL),
    (2,   'Cool',               'Running',           'Cool',               NULL),
    (3,   'Fill',               'Running',           'Fill',               NULL),
    (4,   'Mix',                'Running',           'Mix',                NULL),
    (5,   'Transfer',           'Running',           'Transfer',           NULL),

    -- ========================================================================
    -- Unplanned Downtime (Pilot code 100)
    -- ========================================================================
    (100, 'Unplanned Downtime', 'UnplannedDowntime', 'Unplanned Downtime', NULL),

    -- ========================================================================
    -- Idle/Blocked (Pilot codes 200-299)
    -- Note: Pilot classifies Blocked as Idle, MES Core has dedicated Blocked type
    -- ========================================================================
    (200, 'Idle',               'Idle',              'Idle',               NULL),
    (202, 'Blocked',            'Idle',              'Blocked',            'Pilot classifies as Idle, MES Core as Blocked (is_downtime=true)'),

    -- ========================================================================
    -- Planned Downtime (Pilot codes 300-399)
    -- ========================================================================
    (300, 'Planned Downtime',   'PlannedDowntime',   'Planned Downtime',   NULL),
    (301, 'Changeover',         'PlannedDowntime',   'Changeover',         NULL),
    (305, 'CIP',                'PlannedDowntime',   'CIP',                NULL),
    (306, 'Cleaning',           'PlannedDowntime',   'Cleaning',           NULL),

    -- ========================================================================
    -- Unknown (using -1 as code placeholder)
    -- 15.5% of records in QuestDB - investigate PLC/gateway communication
    -- ========================================================================
    (-1,  'Unknown',            'Unknown',           'Unknown',            '15.5% of records - investigate PLC/gateway communication')

) AS v(pilot_state_code, pilot_state_name, pilot_state_type, mes_state_name, notes)
JOIN mes_core.state_definition sd ON sd.state_name = v.mes_state_name
ON CONFLICT (pilot_state_code) DO UPDATE SET
    pilot_state_name = EXCLUDED.pilot_state_name,
    pilot_state_type = EXCLUDED.pilot_state_type,
    mes_state_id = EXCLUDED.mes_state_id,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;
