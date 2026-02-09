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
    sl.state_id,
    sl.state_name,
    sl.state_type_id,
    sl.state_type_name,
    st.is_downtime,
    sl.logged_at AS state_start,
    sl.downtime_reason_id,
    sl.downtime_reason_name,
    sl.additional_info,
    sl.logged_by
FROM mes_core.state_log sl
LEFT JOIN mes_core.state_type st ON st.state_type_id = sl.state_type_id
WHERE sl.removed IS DISTINCT FROM TRUE
ORDER BY sl.asset_id, sl.logged_at DESC;

COMMENT ON VIEW mes_core.vw_state_active IS 'Latest active state per asset, including downtime status.';

-- ===============================================================
-- View: vw_state_duration_hourly
-- Description: Summarizes state durations by asset and state type, hourly
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_state_duration_hourly AS
WITH timeline AS (
    SELECT asset_id, asset_name, state_type_name, start_time, end_time
    FROM mes_core.vw_state_timeline
    WHERE removed IS DISTINCT FROM TRUE
      AND end_time IS NOT NULL
),
bucketed AS (
    SELECT
        t.asset_id,
        t.asset_name,
        t.state_type_name,
        bucket AS hour,
        EXTRACT(EPOCH FROM (
            LEAST(t.end_time, bucket + INTERVAL '1 hour')
            - GREATEST(t.start_time, bucket)
        )) AS clipped_duration
    FROM timeline t
    CROSS JOIN LATERAL generate_series(
        time_bucket('1 hour', t.start_time),
        time_bucket('1 hour', t.end_time - INTERVAL '1 microsecond'),
        INTERVAL '1 hour'
    ) AS bucket
)
SELECT
    asset_id,
    asset_name,
    state_type_name,
    hour,
    SUM(clipped_duration) AS total_duration_seconds
FROM bucketed
GROUP BY
    asset_id,
    asset_name,
    state_type_name,
    hour;

COMMENT ON VIEW mes_core.vw_state_duration_hourly IS 'Summarizes state durations by asset and state type, hourly. Uses boundary-splitting to correctly attribute cross-bucket states.';

-- ===============================================================
-- View: vw_state_duration_daily
-- Description: Summarizes state durations by asset and state type, daily
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_state_duration_daily AS
WITH timeline AS (
    SELECT asset_id, asset_name, state_type_name, start_time, end_time
    FROM mes_core.vw_state_timeline
    WHERE removed IS DISTINCT FROM TRUE
      AND end_time IS NOT NULL
),
bucketed AS (
    SELECT
        t.asset_id,
        t.asset_name,
        t.state_type_name,
        bucket AS day,
        EXTRACT(EPOCH FROM (
            LEAST(t.end_time, bucket + INTERVAL '1 day')
            - GREATEST(t.start_time, bucket)
        )) AS clipped_duration
    FROM timeline t
    CROSS JOIN LATERAL generate_series(
        time_bucket('1 day', t.start_time),
        time_bucket('1 day', t.end_time - INTERVAL '1 microsecond'),
        INTERVAL '1 day'
    ) AS bucket
)
SELECT
    asset_id,
    asset_name,
    state_type_name,
    day,
    SUM(clipped_duration) AS total_duration_seconds
FROM bucketed
GROUP BY
    asset_id,
    asset_name,
    state_type_name,
    day;

COMMENT ON VIEW mes_core.vw_state_duration_daily IS 'Summarizes state durations by asset and state type, daily. Uses boundary-splitting to correctly attribute cross-bucket states.';

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

DROP VIEW IF EXISTS mes_core.vw_production_log;
CREATE OR REPLACE VIEW mes_core.vw_production_log AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pl.start_ts,
    pl.end_ts,
    SUM(CASE WHEN cl.count_type_name = 'GoodCount' THEN cl.quantity ELSE 0 END) AS good_count,
    SUM(CASE WHEN cl.count_type_name = 'ScrapCount' THEN cl.quantity ELSE 0 END) AS scrap_count,
    SUM(CASE WHEN cl.count_type_name = 'RejectCount' THEN cl.quantity ELSE 0 END) AS reject_count,
    SUM(CASE WHEN cl.count_type_name = 'InfeedCount' THEN cl.quantity ELSE 0 END) AS infeed_count,
    SUM(CASE WHEN cl.count_type_name IN ('GoodCount','ScrapCount','RejectCount') THEN cl.quantity ELSE 0 END) AS total_count,
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

COMMENT ON VIEW mes_core.vw_production_log IS 'Full production log entries with per-type count breakdown. total_count = Good + Scrap + Reject (output total, excludes Infeed/Pallet).';

-- ===============================================================
-- View: vw_production_current
-- Description: Currently active (open) production logs
-- ===============================================================

DROP VIEW IF EXISTS mes_core.vw_production_current;
CREATE OR REPLACE VIEW mes_core.vw_production_current AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    pl.start_ts,
    SUM(CASE WHEN cl.count_type_name = 'GoodCount' THEN cl.quantity ELSE 0 END) AS good_count,
    SUM(CASE WHEN cl.count_type_name = 'ScrapCount' THEN cl.quantity ELSE 0 END) AS scrap_count,
    SUM(CASE WHEN cl.count_type_name = 'RejectCount' THEN cl.quantity ELSE 0 END) AS reject_count,
    SUM(CASE WHEN cl.count_type_name = 'InfeedCount' THEN cl.quantity ELSE 0 END) AS infeed_count,
    SUM(CASE WHEN cl.count_type_name IN ('GoodCount','ScrapCount','RejectCount') THEN cl.quantity ELSE 0 END) AS total_count,
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

COMMENT ON VIEW mes_core.vw_production_current IS 'Currently active (open) production logs with per-type count breakdown. total_count = Good + Scrap + Reject (output total).';

-- ===============================================================
-- View: vw_production_yield
-- Description: Yield calculation by production log
-- ===============================================================

DROP VIEW IF EXISTS mes_core.vw_production_yield;
CREATE OR REPLACE VIEW mes_core.vw_production_yield AS
SELECT
    pl.production_log_id,
    pl.asset_id,
    pl.asset_name,
    pl.product_id,
    pl.product_name,
    SUM(CASE WHEN cl.count_type_name = 'GoodCount' THEN cl.quantity ELSE 0 END) AS good_quantity,
    SUM(CASE WHEN cl.count_type_name IN ('GoodCount', 'ScrapCount', 'RejectCount') THEN cl.quantity ELSE 0 END) AS produced_quantity,
    CASE
        WHEN SUM(CASE WHEN cl.count_type_name IN ('GoodCount', 'ScrapCount', 'RejectCount') THEN cl.quantity ELSE 0 END) > 0
        THEN ROUND(
            SUM(CASE WHEN cl.count_type_name = 'GoodCount' THEN cl.quantity ELSE 0 END)
            / SUM(CASE WHEN cl.count_type_name IN ('GoodCount', 'ScrapCount', 'RejectCount') THEN cl.quantity ELSE 0 END) * 100, 2)
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

COMMENT ON VIEW mes_core.vw_production_yield IS 'Yield calculation by production log. produced_quantity = Good + Scrap + Reject (excludes Infeed/Pallet). yield_percent = Good / Produced * 100.';

-- ===============================================================
-- View: vw_production_throughput_rate
-- Description: Throughput and performance percent based on actual vs ideal rates
-- ===============================================================

DROP VIEW IF EXISTS mes_core.vw_production_throughput_rate;
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
    COALESCE(SUM(cl.quantity) FILTER (WHERE cl.count_type_name = 'GoodCount'), 0) AS good_count,
    CASE
        WHEN EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts)) > 0
        THEN ROUND(COALESCE(SUM(cl.quantity) FILTER (WHERE cl.count_type_name = 'GoodCount'), 0) / EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts)), 4)
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
        THEN ROUND((COALESCE(SUM(cl.quantity) FILTER (WHERE cl.count_type_name = 'GoodCount'), 0) / EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts))) / (1.0 / pd.ideal_cycle_time) * 100, 2)
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

COMMENT ON VIEW mes_core.vw_production_throughput_rate IS 'Throughput and performance percent based on actual vs ideal rates. Uses only GoodCount for rate calculations.';

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
  AND pl.removed IS DISTINCT FROM TRUE
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
WHERE ml.in_tolerance = false
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
    (SELECT string_agg(sln.note, '; ' ORDER BY sln.note_id)
     FROM mes_core.state_log_note sln
     WHERE sln.state_log_id = sl.state_log_id
       AND sln.removed IS DISTINCT FROM TRUE) AS note,
    sl.logged_at
FROM mes_core.state_log sl
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
    (SELECT string_agg(pln.note, '; ' ORDER BY pln.note_id)
     FROM mes_core.production_log_note pln
     WHERE pln.production_log_id = pl.production_log_id
       AND pln.removed IS DISTINCT FROM TRUE) AS note,
    pl.logged_at
FROM mes_core.production_log pl
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
    (SELECT string_agg(cln.note, '; ' ORDER BY cln.note_id)
     FROM mes_core.count_log_note cln
     WHERE cln.count_log_id = cl.count_log_id
       AND cln.removed IS DISTINCT FROM TRUE) AS note,
    cl.logged_at
FROM mes_core.count_log cl
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
    (SELECT string_agg(mln.note, '; ' ORDER BY mln.note_id)
     FROM mes_core.measurement_log_note mln
     WHERE mln.measurement_log_id = ml.measurement_log_id
       AND mln.removed IS DISTINCT FROM TRUE) AS note,
    ml.logged_at
FROM mes_core.measurement_log ml
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
    (SELECT string_agg(kln.note, '; ' ORDER BY kln.note_id)
     FROM mes_core.kpi_log_note kln
     WHERE kln.kpi_log_id = kl.kpi_log_id
       AND kln.removed IS DISTINCT FROM TRUE) AS note,
    kl.logged_at
FROM mes_core.kpi_log kl
WHERE kl.removed IS DISTINCT FROM TRUE;

COMMENT ON VIEW mes_core.vw_unified_event_log IS 'Unified log combining state, production, count, measurement, and KPI events. WARNING: Always filter by logged_at or asset_id to avoid full table scans across 5 hypertables.';

-- ===============================================================
-- DATA QUALITY MONITORING VIEWS
-- ===============================================================
-- These views help identify data quality issues, particularly
-- when edge systems fail to provide complete product information.
-- ===============================================================

-- ===============================================================
-- View: vw_dq_unknown_product_counts
-- Description: Count log entries with Unknown product (product_id = 1)
-- Use: Monitor data quality - high counts indicate edge data issues
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_dq_unknown_product_counts AS
SELECT
    cl.count_log_id,
    cl.asset_id,
    cl.asset_name,
    cl.count_type_id,
    cl.count_type_name,
    cl.quantity,
    cl.production_log_id,
    cl.additional_info,
    cl.logged_by,
    cl.logged_at
FROM mes_core.count_log cl
WHERE cl.product_id = 1  -- Reserved Unknown product ID
  AND cl.removed IS DISTINCT FROM TRUE;

COMMENT ON VIEW mes_core.vw_dq_unknown_product_counts IS 'Data Quality: Count log entries logged against Unknown product (ID=1). High counts indicate missing ProductId from edge equipment. Investigate tag configuration.';

-- ===============================================================
-- View: vw_dq_unknown_product_summary_hourly
-- Description: Hourly summary of Unknown product counts by asset
-- Use: Dashboard widget for data quality monitoring
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_dq_unknown_product_summary_hourly AS
SELECT
    cl.asset_id,
    cl.asset_name,
    cl.count_type_name,
    time_bucket(INTERVAL '1 hour', cl.logged_at) AS hour,
    COUNT(*) AS unknown_count_events,
    SUM(cl.quantity) AS unknown_quantity_total
FROM mes_core.count_log cl
WHERE cl.product_id = 1  -- Reserved Unknown product ID
  AND cl.removed IS DISTINCT FROM TRUE
GROUP BY
    cl.asset_id,
    cl.asset_name,
    cl.count_type_name,
    hour
ORDER BY hour DESC, unknown_count_events DESC;

COMMENT ON VIEW mes_core.vw_dq_unknown_product_summary_hourly IS 'Data Quality: Hourly summary of Unknown product counts by asset. Use for dashboards to track edge data quality issues.';

-- ===============================================================
-- View: vw_dq_unknown_product_summary_daily
-- Description: Daily summary of Unknown product counts by asset
-- Use: Daily data quality report
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_dq_unknown_product_summary_daily AS
WITH daily_totals AS (
    SELECT
        asset_id,
        time_bucket(INTERVAL '1 day', logged_at) AS day,
        COUNT(*) AS total_events
    FROM mes_core.count_log
    WHERE removed IS DISTINCT FROM TRUE
    GROUP BY asset_id, day
),
unknown_counts AS (
    SELECT
        cl.asset_id,
        cl.asset_name,
        cl.count_type_name,
        time_bucket(INTERVAL '1 day', cl.logged_at) AS day,
        COUNT(*) AS unknown_count_events,
        SUM(cl.quantity) AS unknown_quantity_total
    FROM mes_core.count_log cl
    WHERE cl.product_id = 1  -- Reserved Unknown product ID
      AND cl.removed IS DISTINCT FROM TRUE
    GROUP BY
        cl.asset_id,
        cl.asset_name,
        cl.count_type_name,
        day
)
SELECT
    uc.asset_id,
    uc.asset_name,
    uc.count_type_name,
    uc.day,
    uc.unknown_count_events,
    uc.unknown_quantity_total,
    ROUND(uc.unknown_count_events::numeric / NULLIF(dt.total_events, 0) * 100, 2) AS unknown_percent
FROM unknown_counts uc
JOIN daily_totals dt ON dt.asset_id = uc.asset_id AND dt.day = uc.day
ORDER BY uc.day DESC, uc.unknown_count_events DESC;

COMMENT ON VIEW mes_core.vw_dq_unknown_product_summary_daily IS 'Data Quality: Daily summary of Unknown product counts with percentage. Target: 0% unknown. Investigate assets with >5% unknown products.';

-- ===============================================================
-- View: vw_dq_assets_with_unknown_products
-- Description: Assets that have logged counts against Unknown product
-- Use: Identify equipment needing edge configuration fixes
-- ===============================================================

CREATE OR REPLACE VIEW mes_core.vw_dq_assets_with_unknown_products AS
SELECT
    cl.asset_id,
    ad.asset_name,
    at.asset_type_name,
    ad.tag_path,
    COUNT(*) AS unknown_count_events,
    SUM(cl.quantity) AS unknown_quantity_total,
    MIN(cl.logged_at) AS first_unknown_at,
    MAX(cl.logged_at) AS last_unknown_at
FROM mes_core.count_log cl
JOIN mes_core.asset_definition ad ON ad.asset_id = cl.asset_id
LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
WHERE cl.product_id = 1  -- Reserved Unknown product ID
  AND cl.removed IS DISTINCT FROM TRUE
  AND ad.removed IS DISTINCT FROM TRUE
GROUP BY
    cl.asset_id,
    ad.asset_name,
    at.asset_type_name,
    ad.tag_path
ORDER BY unknown_count_events DESC;

COMMENT ON VIEW mes_core.vw_dq_assets_with_unknown_products IS 'Data Quality: Assets that have logged counts against Unknown product. Use tag_path to identify equipment needing ProductId configuration at the edge.';