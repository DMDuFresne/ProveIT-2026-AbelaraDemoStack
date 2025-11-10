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

SET search_path TO public;
