-- ============================================================================
-- 09. KPI DEFINITIONS (Key Performance Indicators)
-- Run Order: 9 of 10
-- Note: No unique constraint on kpi_name - run on fresh database only
-- ============================================================================

INSERT INTO mes_core.kpi_definition (kpi_name, kpi_description, kpi_unit, kpi_formula, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('OEE', 'Standard OEE for fillers, packaging, and palletizing where Good/Reject are meaningful', '%', 'Availability × Performance × Quality', 'seed', NOW(), 'seed', NOW(), false),
    ('Availability', 'Runtime versus scheduled production time', '%', 'Runtime / Planned Production Time', 'seed', NOW(), 'seed', NOW(), false),
    ('Performance', 'Speed efficiency versus ideal cycle time', '%', '(Ideal Cycle Time × Total Count) / Runtime', 'seed', NOW(), 'seed', NOW(), false),
    ('Quality', 'Good output ratio', '%', 'GoodCount / TotalCount', 'seed', NOW(), 'seed', NOW(), false),
    ('MTBF', 'Mean time between failures', 'time', 'Operating Time / Number of Failures', 'seed', NOW(), 'seed', NOW(), false),
    ('MTTR', 'Mean time to repair', 'time', 'Total Repair Time / Number of Failures', 'seed', NOW(), 'seed', NOW(), false),
    ('Bottleneck Indicator', 'Identifies constraint asset by highest blocked/starved time or lowest throughput', 'n/a', 'Rule-based: max blocked time or minimum throughput', 'seed', NOW(), 'seed', NOW(), false),
    ('CIP Cycle Efficiency', 'Planned versus actual CIP duration', '%', 'Planned CIP Time / Actual CIP Time', 'seed', NOW(), 'seed', NOW(), false),
    ('Overfill Waste', 'Tracks excess fill versus target', 'mL/bottle and total', '(Actual Avg NetFill − Target NetFill) × GoodCount', 'seed', NOW(), 'seed', NOW(), false),
    ('Reject Rate', 'Rejects as a percentage of total output', '%', 'RejectCount / TotalCount', 'seed', NOW(), 'seed', NOW(), false);
