-- ============================================================================
-- 04. MEASUREMENT TYPES (Process Variable Categories)
-- Run Order: 4 of 10
-- Note: No unique constraint on measurement_type_name - run on fresh database only
-- ============================================================================

INSERT INTO mes_core.measurement_type (measurement_type_name, measurement_type_description, measurement_type_unit, created_by, created_at, updated_by, updated_at, removed)
VALUES
    ('Temperature', 'Process temperature (vats, tanks, or process points)', '°C', 'seed', NOW(), 'seed', NOW(), false),
    ('Pressure', 'Process pressure (vessels, lines, or pump discharge)', 'bar', 'seed', NOW(), 'seed', NOW(), false),
    ('Flow', 'Volumetric flow rate', 'L/min', 'seed', NOW(), 'seed', NOW(), false),
    ('FlowRate', 'Instantaneous flow rate', 'L/min', 'seed', NOW(), 'seed', NOW(), false),
    ('TotalizedFlow', 'Total volume over time (meter totalizer)', 'L', 'seed', NOW(), 'seed', NOW(), false),
    ('Weight', 'Weight measurement (batching, tank scale, net weight sampling)', 'kg', 'seed', NOW(), 'seed', NOW(), false),
    ('Volume', 'Calculated or derived volume (e.g., from weight and density)', 'L', 'seed', NOW(), 'seed', NOW(), false),
    ('NetFillVolume', 'Net fill result from sampling or QA', 'mL', 'seed', NOW(), 'seed', NOW(), false),
    ('Conductivity', 'Water quality, RO, or utilities conductivity measurement', 'µS/cm', 'seed', NOW(), 'seed', NOW(), false),
    ('RelativeHumidity', 'Ambient relative humidity (from sensor or weather/REST integration)', '%RH', 'seed', NOW(), 'seed', NOW(), false);
