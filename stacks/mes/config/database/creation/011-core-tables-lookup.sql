-- ===============================================================
-- Lookup Tables: mes_core
-- ===============================================================

SET search_path TO mes_core;

-- ===============================================================
-- Table: asset_type
-- Description: Defines categories of assets (e.g., Line, Machine, Cell)
-- ===============================================================

CREATE TABLE asset_type (
    asset_type_id           BIGSERIAL PRIMARY KEY,
    asset_type_name         TEXT UNIQUE NOT NULL,
    asset_type_description  TEXT,
    created_by              TEXT DEFAULT CURRENT_USER,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by              TEXT,
    updated_at              TIMESTAMPTZ,
    removed                 BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.asset_type IS E'@omit delete
Defines categories of assets (e.g., machine, line, cell).';
COMMENT ON COLUMN mes_core.asset_type.asset_type_name IS 'Human-readable name of the asset type.';

CREATE TRIGGER trg_asset_type_updated_at
BEFORE UPDATE ON mes_core.asset_type
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_asset_type
AFTER INSERT OR UPDATE OR DELETE ON mes_core.asset_type
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: state_type
-- Description: Defines operational states (e.g., Running, Down, Idle)
-- ===============================================================

CREATE TABLE state_type (
    state_type_id            BIGSERIAL PRIMARY KEY,
    state_type_name          TEXT UNIQUE NOT NULL,
    state_type_description   TEXT,
    state_type_color         TEXT NOT NULL DEFAULT '#D5D5D5',
    is_downtime              BOOLEAN DEFAULT FALSE,
    created_by               TEXT DEFAULT CURRENT_USER,
    created_at               TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by               TEXT,
    updated_at               TIMESTAMPTZ,
    removed                  BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE state_type IS E'@omit delete
Defines operational states such as Running, Down, Idle.';

CREATE TRIGGER trg_state_type_updated_at
BEFORE UPDATE ON mes_core.state_type
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_state_type
AFTER INSERT OR UPDATE OR DELETE ON mes_core.state_type
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: state_definition
-- Description: Defines specific machine states mapped to categories
-- ===============================================================

CREATE TABLE state_definition (
    state_id            BIGSERIAL PRIMARY KEY,
    state_type_id       BIGINT NOT NULL REFERENCES state_type(state_type_id),
    state_name          TEXT UNIQUE NOT NULL,
    state_description   TEXT,
    state_color         TEXT NOT NULL DEFAULT '#D5D5D5',
    created_by          TEXT DEFAULT CURRENT_USER,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by          TEXT,
    updated_at          TIMESTAMPTZ,
    removed             BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE state_definition IS E'@omit delete
Defines specific machine states mapped to state types.';

CREATE TRIGGER trg_state_definition_updated_at
BEFORE UPDATE ON mes_core.state_definition
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_state_definition
AFTER INSERT OR UPDATE OR DELETE ON mes_core.state_definition
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: downtime_reason
-- Description: Lookup for downtime reasons, mapped to states
-- ===============================================================

CREATE TABLE downtime_reason (
    downtime_reason_id            BIGSERIAL PRIMARY KEY,
    downtime_reason_code          TEXT UNIQUE NOT NULL,
    downtime_reason_name          TEXT NOT NULL,
    downtime_reason_description   TEXT,
    is_planned                    BOOLEAN DEFAULT FALSE,
    created_by                    TEXT DEFAULT CURRENT_USER,
    created_at                    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by                    TEXT,
    updated_at                    TIMESTAMPTZ,
    removed                       BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.downtime_reason IS E'@omit delete
Defines reasons for asset downtime (planned or unplanned).';
COMMENT ON COLUMN mes_core.downtime_reason.downtime_reason_name IS 'Name of the downtime reason.';
COMMENT ON COLUMN mes_core.downtime_reason.is_planned IS 'Indicates if the downtime reason is considered planned.';

CREATE TRIGGER trg_downtime_reason_updated_at
BEFORE UPDATE ON mes_core.downtime_reason
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_downtime_reason
AFTER INSERT OR UPDATE OR DELETE ON mes_core.downtime_reason
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: count_type
-- Description: Defines count types (e.g., Infeed, Outfeed, Waste)
-- ===============================================================

CREATE TABLE count_type (
    count_type_id           BIGSERIAL PRIMARY KEY,
    count_type_name         TEXT NOT NULL,
    count_type_description  TEXT,
    count_type_unit         TEXT NOT NULL,
    created_by              TEXT DEFAULT CURRENT_USER,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by              TEXT,
    updated_at              TIMESTAMPTZ,
    removed                 BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.count_type IS E'@omit delete
Defines types of quantity counts logged against assets (e.g., good, scrap).';
COMMENT ON COLUMN mes_core.count_type.count_type_name IS 'Name of the count type.';

CREATE TRIGGER trg_count_type_updated_at
BEFORE UPDATE ON mes_core.count_type
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_count_type
AFTER INSERT OR UPDATE OR DELETE ON mes_core.count_type
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: measurement_type
-- Description: Defines measurement types (e.g., Weight, Temperature)
-- ===============================================================

CREATE TABLE measurement_type (
    measurement_type_id           BIGSERIAL PRIMARY KEY,
    measurement_type_name         TEXT NOT NULL,
    measurement_type_description  TEXT,
    measurement_type_unit         TEXT NOT NULL,
    created_by                    TEXT DEFAULT CURRENT_USER,
    created_at                    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by                    TEXT,
    updated_at                    TIMESTAMPTZ,
    removed                       BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.measurement_type IS E'@omit delete
Defines types of measurements (e.g., weight, length, pressure).';
COMMENT ON COLUMN mes_core.measurement_type.measurement_type_name IS 'Name of the measurement type.';


CREATE TRIGGER trg_measurement_type_updated_at
BEFORE UPDATE ON mes_core.measurement_type
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_measurement_type
AFTER INSERT OR UPDATE OR DELETE ON mes_core.measurement_type
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: kpi_definition
-- Description: Defines Key Performance Indicators (KPIs)
-- ===============================================================

CREATE TABLE kpi_definition (
    kpi_id           BIGSERIAL PRIMARY KEY,
    kpi_name         TEXT NOT NULL,
    kpi_description  TEXT,
    kpi_unit         TEXT NOT NULL,
    kpi_formula      TEXT,
    created_by       TEXT DEFAULT CURRENT_USER,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by       TEXT,
    updated_at       TIMESTAMPTZ,
    removed          BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.kpi_definition IS E'@omit delete
Defines key performance indicators (KPIs) that can be logged for assets.';
COMMENT ON COLUMN mes_core.kpi_definition.kpi_name IS 'Name of the KPI being measured.';

CREATE TRIGGER trg_kpi_definition_updated_at
BEFORE UPDATE ON mes_core.kpi_definition
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_kpi_definition
AFTER INSERT OR UPDATE OR DELETE ON mes_core.kpi_definition
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();
