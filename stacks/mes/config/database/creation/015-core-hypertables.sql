-- ===============================================================
-- TimescaleDB Hypertable & Compression Setup
-- Scope: Database-level (not schema-specific)
--
-- Author(s):
-- -- Dylan DuFresne
-- ===============================================================

SET search_path TO public;

-- ===============================================================
-- Hypertable: mes_core.state_log
-- Description: One entry per asset state change
-- ===============================================================

SELECT create_hypertable(
    'mes_core.state_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.state_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.state_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.state_log', INTERVAL '3 months');

-- ===============================================================
-- Hypertable: mes_core.production_log
-- Description: One entry per production run
-- ===============================================================

SELECT create_hypertable(
    'mes_core.production_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.production_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.production_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.production_log', INTERVAL '3 months');

-- ===============================================================
-- Hypertable: mes_core.count_log
-- Description: Raw counts, finished goods, scrap counts
-- ===============================================================

SELECT create_hypertable(
    'mes_core.count_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.count_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'production_log_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.count_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.count_log', INTERVAL '3 months');

-- ===============================================================
-- Hypertable: mes_core.measurement_log
-- Description: Product measurements (weight, temp, pH, etc.)
-- ===============================================================

SELECT create_hypertable(
    'mes_core.measurement_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.measurement_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id, product_id, measurement_type_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.measurement_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.measurement_log', INTERVAL '3 months');

-- ===============================================================
-- Hypertable: mes_core.kpi_log
-- Description: KPI measurements such as OEE and scrap rate
-- ===============================================================

SELECT create_hypertable(
    'mes_core.kpi_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.kpi_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.kpi_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.kpi_log', INTERVAL '3 months');

SET search_path TO public;
