-- ===============================================================
-- Core Views: mes_core
-- ===============================================================

-- ===============================================================
-- View: vw_state_timeline
-- Description: State timeline with calculated durations between state changes
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_state_timeline AS
SELECT
    sl.state_log_id,
    sl.asset_id,
    sl.asset_name,
    sl.state_id,
    sl.state_name,
    sl.state_type_id,
    sl.state_type_name,
    st.is_downtime,
    sl.downtime_reason_id,
    sl.downtime_reason_code,
    sl.downtime_reason_name,
    dr.is_planned,
    sl.logged_at AS start_time,
    LEAD(sl.logged_at) OVER (PARTITION BY sl.asset_id ORDER BY sl.logged_at) AS end_time,
    EXTRACT(EPOCH FROM (LEAD(sl.logged_at) OVER (PARTITION BY sl.asset_id ORDER BY sl.logged_at) - sl.logged_at)) AS duration_seconds,
    sl.additional_info,
    sl.logged_by,
    sl.updated_by,
    sl.updated_at,
    sl.removed
FROM mes_core.state_log sl
LEFT JOIN mes_core.state_type st ON st.state_type_id = sl.state_type_id
LEFT JOIN mes_core.downtime_reason dr ON dr.downtime_reason_id = sl.downtime_reason_id
WHERE sl.removed IS DISTINCT FROM TRUE;

COMMENT ON VIEW mes_core.vw_state_timeline IS 'State timeline with calculated durations between state changes.';

-- ===============================================================
-- View: vw_state_active
-- Description: Latest active state per asset
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_state_active AS
SELECT DISTINCT ON (sl.asset_id)
    sl.asset_id,
    sl.asset_name,
    sl.state_log_id,
    sl.state_name,
    sl.state_type_name,
    sl.logged_at AS state_start,
    sl.downtime_reason_id,
    sl.downtime_reason_name,
    sl.additional_info,
    sl.logged_by
FROM mes_core.state_log sl
WHERE sl.removed IS DISTINCT FROM TRUE
ORDER BY sl.asset_id, sl.logged_at DESC;

COMMENT ON VIEW mes_core.vw_state_active IS 'Latest active state per asset.';

-- ===============================================================
-- View: vw_state_duration_hourly
-- Description: Summarizes state durations by asset and state type, hourly
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_state_duration_hourly AS
SELECT
    asset_id,
    asset_name,
    state_type_name,
    time_bucket(INTERVAL '1 hour', start_time) AS hour,
    SUM(duration_seconds) AS total_duration_seconds
FROM mes_core.vw_state_timeline
WHERE removed IS DISTINCT FROM TRUE
GROUP BY
    asset_id,
    asset_name,
    state_type_name,
    hour;

COMMENT ON VIEW mes_core.vw_state_duration_hourly IS 'Summarizes state durations by asset and state type, hourly.';

-- ===============================================================
-- View: vw_state_duration_daily
-- Description: Summarizes state durations by asset and state type, daily
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_state_duration_daily AS
SELECT
    asset_id,
    asset_name,
    state_type_name,
    time_bucket(INTERVAL '1 day', start_time) AS day,
    SUM(duration_seconds) AS total_duration_seconds
FROM mes_core.vw_state_timeline
WHERE removed IS DISTINCT FROM TRUE
GROUP BY
    asset_id,
    asset_name,
    state_type_name,
    day;

COMMENT ON VIEW mes_core.vw_state_duration_daily IS 'Summarizes state durations by asset and state type, daily.';

-- ===============================================================
-- View: vw_state_downtime_events
-- Description: Lists all downtime events based on is_downtime or downtime_reason
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_state_downtime_events AS
SELECT
    state_log_id,
    asset_id,
    asset_name,
    state_name,
    state_type_name,
    is_downtime,
    downtime_reason_id,
    downtime_reason_code,
    downtime_reason_name,
    is_planned,
    start_time,
    end_time,
    duration_seconds,
    additional_info,
    logged_by,
    updated_by,
    updated_at,
    removed
FROM mes_core.vw_state_timeline
WHERE removed IS DISTINCT FROM TRUE
  AND (is_downtime = TRUE OR downtime_reason_id IS NOT NULL);

COMMENT ON VIEW mes_core.vw_state_downtime_events IS 'Lists all downtime events based on is_downtime or downtime_reason.';

-- ===============================================================
-- View: vw_production_log
-- Description: Full production log entries with asset and product names
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_production_log AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pl.start_ts,
    pl.end_ts,
    COALESCE(SUM(cl.quantity), 0) AS total_count,
    pl.additional_info,
    pl.logged_by,
    pl.logged_at,
    pl.updated_by,
    pl.updated_at,
    pl.removed
FROM mes_core.production_log pl
LEFT JOIN mes_core.count_log cl ON cl.production_log_id = pl.production_log_id AND cl.removed IS DISTINCT FROM TRUE
WHERE pl.removed IS DISTINCT FROM TRUE
GROUP BY
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pl.start_ts,
    pl.end_ts,
    pl.additional_info,
    pl.logged_by,
    pl.logged_at,
    pl.updated_by,
    pl.updated_at,
    pl.removed;

COMMENT ON VIEW mes_core.vw_production_log IS 'Full production log entries with asset and product names.';

-- ===============================================================
-- View: vw_production_current
-- Description: Currently active (open) production logs
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_production_current AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pl.start_ts,
    COALESCE(SUM(cl.quantity), 0) AS total_count,
    pl.additional_info,
    pl.logged_by,
    pl.logged_at
FROM mes_core.production_log pl
LEFT JOIN mes_core.count_log cl ON cl.production_log_id = pl.production_log_id AND cl.removed IS DISTINCT FROM TRUE
WHERE pl.end_ts IS NULL
  AND pl.removed IS DISTINCT FROM TRUE
GROUP BY
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pl.start_ts,
    pl.additional_info,
    pl.logged_by,
    pl.logged_at;

COMMENT ON VIEW mes_core.vw_production_current IS 'Currently active (open) production logs.';

-- ===============================================================
-- View: vw_production_yield
-- Description: Yield calculation by production log
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_production_yield AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    SUM(CASE WHEN cl.count_type_name ILIKE 'good' THEN cl.quantity ELSE 0 END) AS good_quantity,
    SUM(cl.quantity) AS total_quantity,
    CASE
        WHEN SUM(cl.quantity) > 0
        THEN ROUND(SUM(CASE WHEN cl.count_type_name ILIKE 'good' THEN cl.quantity ELSE 0 END) / SUM(cl.quantity) * 100, 2)
        ELSE NULL
    END AS yield_percent
FROM mes_core.production_log pl
LEFT JOIN mes_core.count_log cl ON cl.production_log_id = pl.production_log_id
  AND cl.removed IS DISTINCT FROM TRUE
WHERE pl.removed IS DISTINCT FROM TRUE
GROUP BY
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name;

COMMENT ON VIEW mes_core.vw_production_yield IS 'Yield calculation by production log.';

-- ===============================================================
-- View: vw_production_throughput_rate
-- Description: Throughput and performance percent based on actual vs ideal rates
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_production_throughput_rate AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pd.ideal_cycle_time,
    pl.start_ts,
    pl.end_ts,
    EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts)) AS run_duration_seconds,
    COALESCE(SUM(cl.quantity), 0) AS total_count,
    CASE
        WHEN EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts)) > 0
        THEN ROUND(COALESCE(SUM(cl.quantity), 0) / EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts)), 4)
        ELSE NULL
    END AS actual_rate,
    CASE
        WHEN pd.ideal_cycle_time > 0
        THEN ROUND(1.0 / pd.ideal_cycle_time, 4)
        ELSE NULL
    END AS ideal_rate,
    CASE
        WHEN pd.ideal_cycle_time > 0
         AND EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts)) > 0
        THEN ROUND((COALESCE(SUM(cl.quantity), 0) / EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts))) / (1.0 / pd.ideal_cycle_time) * 100, 2)
        ELSE NULL
    END AS performance_percent
FROM mes_core.production_log pl
LEFT JOIN mes_core.product_definition pd ON pd.product_id = pl.product_id
LEFT JOIN mes_core.count_log cl ON cl.production_log_id = pl.production_log_id AND cl.removed IS DISTINCT FROM TRUE
WHERE pl.removed IS DISTINCT FROM TRUE
  AND pl.end_ts IS NOT NULL
GROUP BY
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pd.ideal_cycle_time,
    pl.start_ts,
    pl.end_ts;

COMMENT ON VIEW mes_core.vw_production_throughput_rate IS 'Throughput and performance percent based on actual vs ideal rates.';

-- ===============================================================
-- View: vw_production_state_summary
-- Description: State category duration summary per production run
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_production_state_summary AS
WITH state_durations AS (
    SELECT
        pl.production_log_id,
        pl.asset_id,
        pl.asset_name,
        pl.product_id,
        pl.product_name,
        sl.state_type_name,
        sl.logged_at AS start_time,
        LEAD(sl.logged_at) OVER (PARTITION BY sl.asset_id ORDER BY sl.logged_at) AS end_time
    FROM mes_core.production_log pl
    JOIN mes_core.state_log sl
      ON sl.asset_id = pl.asset_id
      AND sl.logged_at >= pl.start_ts
      AND (pl.end_ts IS NULL OR sl.logged_at < pl.end_ts)
    WHERE pl.removed IS DISTINCT FROM TRUE
      AND sl.removed IS DISTINCT FROM TRUE
)
SELECT
    production_log_id,
    asset_id,
    asset_name,
    product_id,
    product_name,
    state_type_name,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time))) AS duration_seconds
FROM state_durations
WHERE end_time IS NOT NULL
GROUP BY
    production_log_id,
    asset_id,
    asset_name,
    product_id,
    product_name,
    state_type_name;

COMMENT ON VIEW mes_core.vw_production_state_summary IS 'State category duration summary per production run.';

-- ===============================================================
-- View: vw_production_count_summary
-- Description: Summarizes counts by type during production runs
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_production_count_summary AS
SELECT
    cl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    cl.product_id,
    cl.product_name,
    cl.count_type_id,
    cl.count_type_name,
    SUM(cl.quantity) AS total_quantity
FROM mes_core.count_log cl
LEFT JOIN mes_core.production_log pl ON pl.production_log_id = cl.production_log_id
WHERE cl.removed IS DISTINCT FROM TRUE
GROUP BY
    cl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    cl.product_id,
    cl.product_name,
    cl.count_type_id,
    cl.count_type_name;

COMMENT ON VIEW mes_core.vw_production_count_summary IS 'Summarizes counts by type during production runs.';

-- ===============================================================
-- View: vw_production_measurement_summary
-- Description: Summarizes measurements during production runs
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_production_measurement_summary AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    ml.product_id,
    ml.product_name,
    ml.measurement_type_id,
    ml.measurement_type_name,
    ml.unit_of_measure,
    COUNT(*) AS sample_count,
    AVG(ml.actual_value) AS avg_actual_value,
    MIN(ml.actual_value) AS min_actual_value,
    MAX(ml.actual_value) AS max_actual_value
FROM mes_core.production_log pl
JOIN mes_core.measurement_log ml
  ON ml.asset_id = pl.asset_id
  AND ml.logged_at >= pl.start_ts
  AND (pl.end_ts IS NULL OR ml.logged_at < pl.end_ts)
WHERE ml.removed IS DISTINCT FROM TRUE
GROUP BY
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    ml.product_id,
    ml.product_name,
    ml.measurement_type_id,
    ml.measurement_type_name,
    ml.unit_of_measure;

COMMENT ON VIEW mes_core.vw_production_measurement_summary IS 'Summarizes measurements during production runs.';

-- ===============================================================
-- View: vw_measurement_summary_by_product
-- Description: Summarizes measurement data per product
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_measurement_summary_by_product AS
SELECT
    ml.product_id,
    ml.product_name,
    ml.measurement_type_id,
    ml.measurement_type_name,
    ml.unit_of_measure,
    COUNT(*) AS sample_count,
    AVG(ml.actual_value) AS avg_actual_value,
    MIN(ml.actual_value) AS min_actual_value,
    MAX(ml.actual_value) AS max_actual_value
FROM mes_core.measurement_log ml
WHERE ml.removed IS DISTINCT FROM TRUE
GROUP BY
    ml.product_id,
    ml.product_name,
    ml.measurement_type_id,
    ml.measurement_type_name,
    ml.unit_of_measure;

COMMENT ON VIEW mes_core.vw_measurement_summary_by_product IS 'Summarizes measurement data per product.';

-- ===============================================================
-- View: vw_measurement_out_of_tolerance
-- Description: Identifies measurements outside tolerance
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_measurement_out_of_tolerance AS
SELECT
    ml.measurement_log_id,
    ml.asset_id,
    ml.asset_name,
    ml.product_id,
    ml.product_name,
    ml.measurement_type_id,
    ml.measurement_type_name,
    ml.unit_of_measure,
    ml.target_value,
    ml.actual_value,
    ml.tolerance,
    ml.in_tolerance,
    ml.logged_by,
    ml.logged_at,
    ml.additional_info
FROM mes_core.measurement_log ml
WHERE ml.in_tolerance IS DISTINCT FROM TRUE
AND ml.removed IS DISTINCT FROM TRUE;

COMMENT ON VIEW mes_core.vw_measurement_out_of_tolerance IS 'Identifies measurements outside tolerance.';

-- ===============================================================
-- View: vw_kpi_latest
-- Description: Latest KPI measurement per asset and KPI
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_kpi_latest AS
SELECT DISTINCT ON (kl.asset_id, kl.kpi_id)
    kl.asset_id,
    kl.asset_name,
    kl.kpi_id,
    kl.kpi_name,
    kl.kpi_value,
    kl.start_ts,
    kl.end_ts,
    kl.logged_at,
    kl.logged_by
FROM mes_core.kpi_log kl
WHERE kl.removed IS DISTINCT FROM TRUE
ORDER BY kl.asset_id, kl.kpi_id, kl.logged_at DESC;

COMMENT ON VIEW mes_core.vw_kpi_latest IS 'Latest KPI measurement per asset and KPI.';

-- ===============================================================
-- View: vw_unified_event_log
-- Description: Unified log combining state, production, count, measurement, and KPI events
--
-- ⚠️ WARNING: This view queries 5 hypertables with UNION ALL.
-- ⚠️ ALWAYS filter by logged_at or asset_id to avoid full table scans!
-- ⚠️ Example: WHERE logged_at >= NOW() - INTERVAL '7 days'
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_unified_event_log AS
SELECT
    'state' AS event_type,
    sl.state_log_id AS event_id,
    sl.asset_id,
    NULL::BIGINT AS product_id,
    sl.state_name AS value,
    NULL::TEXT AS unit,
    sl.logged_at AS start_ts,
    NULL::TIMESTAMPTZ AS end_ts,
    sln.note,
    sl.logged_at
FROM mes_core.state_log sl
LEFT JOIN mes_core.state_log_note sln ON sln.state_log_id = sl.state_log_id AND sln.removed IS DISTINCT FROM TRUE
WHERE sl.removed IS DISTINCT FROM TRUE

UNION ALL

SELECT
    'production' AS event_type,
    pl.production_log_id AS event_id,
    pl.asset_id,
    pl.product_id,
    NULL::TEXT AS value,
    NULL::TEXT AS unit,
    pl.start_ts,
    pl.end_ts,
    pln.note,
    pl.logged_at
FROM mes_core.production_log pl
LEFT JOIN mes_core.production_log_note pln ON pln.production_log_id = pl.production_log_id AND pln.removed IS DISTINCT FROM TRUE
WHERE pl.removed IS DISTINCT FROM TRUE

UNION ALL

SELECT
    'count' AS event_type,
    cl.count_log_id AS event_id,
    cl.asset_id,
    cl.product_id,
    cl.quantity::TEXT AS value,
    cl.count_type_name AS unit,
    cl.logged_at AS start_ts,
    NULL::TIMESTAMPTZ AS end_ts,
    cln.note,
    cl.logged_at
FROM mes_core.count_log cl
LEFT JOIN mes_core.count_log_note cln ON cln.count_log_id = cl.count_log_id AND cln.removed IS DISTINCT FROM TRUE
WHERE cl.removed IS DISTINCT FROM TRUE

UNION ALL

SELECT
    'measurement' AS event_type,
    ml.measurement_log_id AS event_id,
    ml.asset_id,
    ml.product_id,
    ml.actual_value::TEXT AS value,
    ml.unit_of_measure AS unit,
    ml.logged_at AS start_ts,
    NULL::TIMESTAMPTZ AS end_ts,
    mln.note,
    ml.logged_at
FROM mes_core.measurement_log ml
LEFT JOIN mes_core.measurement_log_note mln ON mln.measurement_log_id = ml.measurement_log_id AND mln.removed IS DISTINCT FROM TRUE
WHERE ml.removed IS DISTINCT FROM TRUE

UNION ALL

SELECT
    'kpi' AS event_type,
    kl.kpi_log_id AS event_id,
    kl.asset_id,
    NULL::BIGINT AS product_id,
    kl.kpi_value::TEXT AS value,
    kl.kpi_name AS unit,
    kl.start_ts,
    kl.end_ts,
    kln.note,
    kl.logged_at
FROM mes_core.kpi_log kl
LEFT JOIN mes_core.kpi_log_note kln ON kln.kpi_log_id = kl.kpi_log_id AND kln.removed IS DISTINCT FROM TRUE
WHERE kl.removed IS DISTINCT FROM TRUE;

COMMENT ON VIEW mes_core.vw_unified_event_log IS 'Unified log combining state, production, count, measurement, and KPI events. WARNING: Always filter by logged_at or asset_id to avoid full table scans across 5 hypertables.';