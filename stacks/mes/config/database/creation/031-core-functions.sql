-- ===============================================================
-- Core Functions: mes_core
--
-- Author(s):
-- -- Dylan DuFresne
-- ===============================================================

SET search_path TO mes_core;

-- ===============================================================
-- Function: fn_search_asset_ancestors
-- Description: Recursively finds all ancestor assets for a given asset
-- ===============================================================

CREATE OR REPLACE FUNCTION fn_search_asset_ancestors(
    target_asset_id BIGINT,
    max_level       INT DEFAULT 10
)
RETURNS TABLE (
    level             INT,
    asset_id          BIGINT,
    asset_name        TEXT,
    asset_type_id     BIGINT,
    asset_type_name   TEXT,
    asset_description TEXT,
    parent_asset_id   BIGINT
)
LANGUAGE sql
AS $$
WITH RECURSIVE ancestors AS (
    SELECT
        0 AS level,
        a.asset_id,
        a.asset_name,
        a.asset_type_id,
        at.asset_type_name,
        a.asset_description,
        a.parent_asset_id,
        ARRAY[a.asset_id] AS visited
    FROM mes_core.asset_definition a
    LEFT JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
    WHERE a.asset_id = target_asset_id
      AND a.removed IS DISTINCT FROM TRUE

    UNION ALL

    SELECT
        anc.level + 1,
        a.asset_id,
        a.asset_name,
        a.asset_type_id,
        at.asset_type_name,
        a.asset_description,
        a.parent_asset_id,
        anc.visited || a.asset_id
    FROM mes_core.asset_definition a
    LEFT JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
    JOIN ancestors anc ON a.asset_id = anc.parent_asset_id
    WHERE NOT a.asset_id = ANY(anc.visited)
      AND anc.level + 1 <= max_level
      AND a.removed IS DISTINCT FROM TRUE
)
SELECT
    level,
    asset_id,
    asset_name,
    asset_type_id,
    asset_type_name,
    asset_description,
    parent_asset_id
FROM ancestors
ORDER BY level;
$$;

-- ===============================================================
-- Function: fn_search_asset_descendants
-- Description: Recursively finds all descendant assets for a given asset
-- ===============================================================

-- ===============================================================
-- Function: fn_search_asset_descendants
-- Description: Recursively finds all descendant assets for a given asset
-- ===============================================================

CREATE OR REPLACE FUNCTION fn_search_asset_descendants(
    target_asset_id BIGINT,
    max_level       INT DEFAULT 10
)
RETURNS TABLE (
    level             INT,
    asset_id          BIGINT,
    asset_name        TEXT,
    asset_type_id     BIGINT,
    asset_type_name   TEXT,
    asset_description TEXT,
    parent_asset_id   BIGINT
)
LANGUAGE sql
AS $$
WITH RECURSIVE descendants AS (
    SELECT
        0 AS level,
        a.asset_id,
        a.asset_name,
        a.asset_type_id,
        at.asset_type_name,
        a.asset_description,
        a.parent_asset_id,
        ARRAY[a.asset_id] AS visited
    FROM mes_core.asset_definition a
    LEFT JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
    WHERE a.asset_id = target_asset_id
      AND a.removed IS DISTINCT FROM TRUE

    UNION ALL

    SELECT
        descendants.level + 1,
        a.asset_id,
        a.asset_name,
        a.asset_type_id,
        at.asset_type_name,
        a.asset_description,
        a.parent_asset_id,
        descendants.visited || a.asset_id
    FROM mes_core.asset_definition a
    LEFT JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
    JOIN descendants ON a.parent_asset_id = descendants.asset_id
    WHERE NOT a.asset_id = ANY(descendants.visited)
      AND descendants.level + 1 <= max_level
      AND a.removed IS DISTINCT FROM TRUE
)
SELECT
    level,
    asset_id,
    asset_name,
    asset_type_id,
    asset_type_name,
    asset_description,
    parent_asset_id
FROM descendants
ORDER BY level, asset_id;
$$;

-- ===============================================================
-- Function: fn_get_asset_tree
-- Description: Retrieves full asset tree starting from a root asset
-- ===============================================================

CREATE OR REPLACE FUNCTION fn_get_asset_tree(
    root_asset_id BIGINT,
    max_level     INT DEFAULT 10
)
RETURNS TABLE (
    level             INT,
    asset_id          BIGINT,
    asset_name        TEXT,
    asset_type_name   TEXT,
    asset_description TEXT,
    parent_asset_id   BIGINT
)
LANGUAGE sql
AS $$
WITH RECURSIVE asset_tree AS (
    SELECT
        0 AS level,
        a.asset_id,
        a.asset_name,
        at.asset_type_name,
        a.asset_description,
        a.parent_asset_id,
        ARRAY[a.asset_id] AS visited
    FROM mes_core.asset_definition a
    LEFT JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
    WHERE a.asset_id = root_asset_id
      AND a.removed IS DISTINCT FROM TRUE

    UNION ALL

    SELECT
        t.level + 1,
        a.asset_id,
        a.asset_name,
        at.asset_type_name,
        a.asset_description,
        a.parent_asset_id,
        t.visited || a.asset_id
    FROM mes_core.asset_definition a
    LEFT JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
    JOIN asset_tree t ON a.parent_asset_id = t.asset_id
    WHERE NOT a.asset_id = ANY(t.visited)
      AND t.level + 1 <= max_level
      AND a.removed IS DISTINCT FROM TRUE
)
SELECT
    level,
    asset_id,
    asset_name,
    asset_type_name,
    asset_description,
    parent_asset_id
FROM asset_tree
ORDER BY level, asset_id;
$$;

-- ===============================================================
-- Function: fn_assets_without_state
-- Description: Find assets that have no state log entries
-- ===============================================================

CREATE OR REPLACE FUNCTION fn_assets_without_state()
RETURNS TABLE(
    asset_id BIGINT,
    asset_name TEXT,
    asset_type_name TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        a.asset_id,
        a.asset_name,
        at.asset_type_name,
        a.created_at
    FROM mes_core.asset_definition a
    LEFT JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
    LEFT JOIN (
        SELECT DISTINCT asset_id
        FROM mes_core.state_log
        WHERE removed IS DISTINCT FROM TRUE
    ) sl ON sl.asset_id = a.asset_id
    WHERE sl.asset_id IS NULL
      AND a.removed IS DISTINCT FROM TRUE
    ORDER BY a.created_at DESC;
$$;

COMMENT ON FUNCTION fn_assets_without_state IS 'Returns assets that have no state log entries. Useful for validation after creating new assets.';

-- ===============================================================
-- JSONB Insert Wrapper Functions
-- ===============================================================
-- These functions provide a clean API for inserting into log tables
-- that have JSONB additional_info columns. They accept TEXT for
-- additional_info and cast to JSONB internally.
--
-- Required because Highbyte Intelligence Hub cannot send native
-- JSONB types - it sends JSON as varchar strings.
-- ===============================================================

-- ---------------------------------------------------------------
-- Function: fn_insert_kpi_log
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_core.fn_insert_kpi_log(
    p_asset_id        BIGINT,
    p_asset_name      TEXT,
    p_kpi_id          BIGINT,
    p_kpi_name        TEXT,
    p_kpi_value       NUMERIC,
    p_start_ts        TIMESTAMPTZ,
    p_end_ts          TIMESTAMPTZ,
    p_additional_info TEXT DEFAULT NULL,
    p_kpi_log_id      BIGINT DEFAULT NULL
)
RETURNS SETOF mes_core.kpi_log
LANGUAGE sql
AS $$
    INSERT INTO mes_core.kpi_log (
        kpi_log_id, asset_id, asset_name, kpi_id, kpi_name,
        kpi_value, start_ts, end_ts, additional_info
    ) VALUES (
        COALESCE(p_kpi_log_id, nextval('mes_core.kpi_log_kpi_log_id_seq')),
        p_asset_id, p_asset_name, p_kpi_id, p_kpi_name,
        p_kpi_value, p_start_ts, p_end_ts,
        CASE WHEN p_additional_info IS NOT NULL THEN p_additional_info::jsonb ELSE NULL END
    )
    RETURNING *;
$$;

COMMENT ON FUNCTION mes_core.fn_insert_kpi_log IS
'Wrapper for inserting kpi_log records. Accepts additional_info as TEXT and casts to JSONB.';

-- ---------------------------------------------------------------
-- Function: fn_insert_state_log
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_core.fn_insert_state_log(
    p_asset_id            BIGINT,
    p_asset_name          TEXT,
    p_state_id            BIGINT,
    p_state_name          TEXT,
    p_state_type_id       BIGINT,
    p_state_type_name     TEXT,
    p_from_state_id       BIGINT DEFAULT NULL,
    p_additional_info     TEXT DEFAULT NULL,
    p_downtime_reason_id  BIGINT DEFAULT NULL,
    p_downtime_reason_code TEXT DEFAULT NULL,
    p_downtime_reason_name TEXT DEFAULT NULL,
    p_state_log_id        BIGINT DEFAULT NULL
)
RETURNS SETOF mes_core.state_log
LANGUAGE sql
AS $$
    INSERT INTO mes_core.state_log (
        state_log_id, asset_id, asset_name, state_id, state_name,
        state_type_id, state_type_name, from_state_id, additional_info,
        downtime_reason_id, downtime_reason_code, downtime_reason_name
    ) VALUES (
        COALESCE(p_state_log_id, nextval('mes_core.state_log_state_log_id_seq')),
        p_asset_id, p_asset_name, p_state_id, p_state_name,
        p_state_type_id, p_state_type_name, p_from_state_id,
        CASE WHEN p_additional_info IS NOT NULL THEN p_additional_info::jsonb ELSE NULL END,
        p_downtime_reason_id, p_downtime_reason_code, p_downtime_reason_name
    )
    RETURNING *;
$$;

COMMENT ON FUNCTION mes_core.fn_insert_state_log IS
'Wrapper for inserting state_log records. Accepts additional_info as TEXT and casts to JSONB.';

-- ---------------------------------------------------------------
-- Function: fn_insert_production_log
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_core.fn_insert_production_log(
    p_asset_id            BIGINT,
    p_asset_name          TEXT,
    p_product_id          BIGINT,
    p_product_name        TEXT,
    p_product_family_id   BIGINT,
    p_product_family_name TEXT,
    p_start_ts            TIMESTAMPTZ,
    p_end_ts              TIMESTAMPTZ DEFAULT NULL,
    p_additional_info     TEXT DEFAULT NULL,
    p_production_log_id   BIGINT DEFAULT NULL
)
RETURNS SETOF mes_core.production_log
LANGUAGE sql
AS $$
    INSERT INTO mes_core.production_log (
        production_log_id, asset_id, asset_name, product_id, product_name,
        product_family_id, product_family_name, start_ts, end_ts, additional_info
    ) VALUES (
        COALESCE(p_production_log_id, nextval('mes_core.production_log_production_log_id_seq')),
        p_asset_id, p_asset_name, p_product_id, p_product_name,
        p_product_family_id, p_product_family_name, p_start_ts, p_end_ts,
        CASE WHEN p_additional_info IS NOT NULL THEN p_additional_info::jsonb ELSE NULL END
    )
    RETURNING *;
$$;

COMMENT ON FUNCTION mes_core.fn_insert_production_log IS
'Wrapper for inserting production_log records. Accepts additional_info as TEXT and casts to JSONB.';

-- ---------------------------------------------------------------
-- Function: fn_insert_count_log
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_core.fn_insert_count_log(
    p_asset_id            BIGINT,
    p_asset_name          TEXT,
    p_production_log_id   BIGINT,
    p_count_type_id       BIGINT,
    p_count_type_name     TEXT,
    p_quantity            NUMERIC,
    p_product_id          BIGINT,
    p_product_name        TEXT,
    p_product_family_id   BIGINT,
    p_product_family_name TEXT,
    p_additional_info     TEXT DEFAULT NULL,
    p_count_log_id        BIGINT DEFAULT NULL
)
RETURNS SETOF mes_core.count_log
LANGUAGE sql
AS $$
    INSERT INTO mes_core.count_log (
        count_log_id, asset_id, asset_name, production_log_id,
        count_type_id, count_type_name, quantity,
        product_id, product_name, product_family_id, product_family_name,
        additional_info
    ) VALUES (
        COALESCE(p_count_log_id, nextval('mes_core.count_log_count_log_id_seq')),
        p_asset_id, p_asset_name, p_production_log_id,
        p_count_type_id, p_count_type_name, p_quantity,
        p_product_id, p_product_name, p_product_family_id, p_product_family_name,
        CASE WHEN p_additional_info IS NOT NULL THEN p_additional_info::jsonb ELSE NULL END
    )
    RETURNING *;
$$;

COMMENT ON FUNCTION mes_core.fn_insert_count_log IS
'Wrapper for inserting count_log records. Accepts additional_info as TEXT and casts to JSONB.';

-- ---------------------------------------------------------------
-- Function: fn_insert_measurement_log
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION mes_core.fn_insert_measurement_log(
    p_asset_id              BIGINT,
    p_asset_name            TEXT,
    p_product_id            BIGINT,
    p_product_name          TEXT,
    p_product_family_id     BIGINT,
    p_product_family_name   TEXT,
    p_measurement_type_id   BIGINT,
    p_measurement_type_name TEXT,
    p_target_value          NUMERIC DEFAULT NULL,
    p_actual_value          NUMERIC DEFAULT NULL,
    p_unit_of_measure       TEXT DEFAULT NULL,
    p_tolerance             NUMERIC DEFAULT 0,
    p_in_tolerance          BOOLEAN DEFAULT NULL,
    p_additional_info       TEXT DEFAULT NULL,
    p_measurement_log_id    BIGINT DEFAULT NULL
)
RETURNS SETOF mes_core.measurement_log
LANGUAGE sql
AS $$
    INSERT INTO mes_core.measurement_log (
        measurement_log_id, asset_id, asset_name, product_id, product_name,
        product_family_id, product_family_name, measurement_type_id, measurement_type_name,
        target_value, actual_value, unit_of_measure, tolerance, in_tolerance,
        additional_info
    ) VALUES (
        COALESCE(p_measurement_log_id, nextval('mes_core.measurement_log_measurement_log_id_seq')),
        p_asset_id, p_asset_name, p_product_id, p_product_name,
        p_product_family_id, p_product_family_name, p_measurement_type_id, p_measurement_type_name,
        p_target_value, p_actual_value, p_unit_of_measure, p_tolerance, p_in_tolerance,
        CASE WHEN p_additional_info IS NOT NULL THEN p_additional_info::jsonb ELSE NULL END
    )
    RETURNING *;
$$;

COMMENT ON FUNCTION mes_core.fn_insert_measurement_log IS
'Wrapper for inserting measurement_log records. Accepts additional_info as TEXT and casts to JSONB.';

SET search_path TO public;
