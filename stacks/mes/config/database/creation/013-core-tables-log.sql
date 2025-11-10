-- ===============================================================
-- Core Event Logging: mes_core
-- ===============================================================

SET search_path TO mes_core;

-- ===============================================================
-- Table: state_log
-- Description: Logs asset state transitions, optionally with downtime reasons
-- ===============================================================

CREATE TABLE state_log (
    state_log_id         BIGINT GENERATED ALWAYS AS IDENTITY,
    asset_id             BIGINT NOT NULL REFERENCES asset_definition(asset_id),
    asset_name           TEXT NOT NULL,
    state_id             BIGINT NOT NULL REFERENCES state_definition(state_id),
    state_name           TEXT NOT NULL,
    state_type_id         BIGINT NOT NULL REFERENCES state_type(state_type_id),
    state_type_name      TEXT NOT NULL,
    from_state_id        BIGINT,
    additional_info      JSONB,
    downtime_reason_id   BIGINT REFERENCES downtime_reason(downtime_reason_id),
    downtime_reason_code TEXT,
    downtime_reason_name TEXT,
    logged_by            TEXT DEFAULT CURRENT_USER,
    logged_at            TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by           TEXT,
    updated_at           TIMESTAMPTZ,
    removed              BOOLEAN DEFAULT FALSE
);

-- State Log Comments
COMMENT ON TABLE mes_core.state_log IS E'@omit delete
Logs asset state transitions, tracking the state type and time. Immutable log - records cannot be deleted via GraphQL API (use soft delete with removed=true).';
COMMENT ON COLUMN mes_core.state_log.state_log_id IS 'Surrogate identity for the state_log record.';
COMMENT ON COLUMN mes_core.state_log.asset_id IS 'Reference to the asset experiencing a state transition.';
COMMENT ON COLUMN mes_core.state_log.asset_name IS 'Snapshot of the asset name at time of state change.';
COMMENT ON COLUMN mes_core.state_log.state_id IS 'FK to the specific state being entered (e.g., Running, Idle).';
COMMENT ON COLUMN mes_core.state_log.state_name IS 'Snapshot of the state name at the time of transition.';
COMMENT ON COLUMN mes_core.state_log.state_type_id IS 'FK to the category of the state (e.g., Operating, Downtime).';
COMMENT ON COLUMN mes_core.state_log.state_type_name IS 'Snapshot of the state type name used for reporting.';
COMMENT ON COLUMN mes_core.state_log.from_state_id IS 'Reference to the previous state_log.state_id for the same asset.';
COMMENT ON COLUMN mes_core.state_log.additional_info IS 'Additional structured metadata such as process values, sensor readings, or context. Not used for notes.';
COMMENT ON COLUMN mes_core.state_log.downtime_reason_id IS 'Optional FK to the reason for downtime if applicable.';
COMMENT ON COLUMN mes_core.state_log.downtime_reason_code IS 'Snapshot of the downtime reason short code.';
COMMENT ON COLUMN mes_core.state_log.downtime_reason_name IS 'Snapshot of the downtime reason name for reporting.';
COMMENT ON COLUMN mes_core.state_log.logged_by IS 'User or system that recorded the state change.';
COMMENT ON COLUMN mes_core.state_log.logged_at IS 'Timestamp when the state change was recorded.';
COMMENT ON COLUMN mes_core.state_log.updated_by IS 'User who last updated this row.';
COMMENT ON COLUMN mes_core.state_log.updated_at IS 'Timestamp of last modification.';
COMMENT ON COLUMN mes_core.state_log.removed IS 'TRUE if the row has been soft-deleted.';

CREATE INDEX idx_state_log_asset_logged_at
ON mes_core.state_log(asset_id, logged_at DESC);

CREATE INDEX idx_state_log_downtime_reason_id
ON mes_core.state_log(downtime_reason_id);

CREATE INDEX idx_state_log_state_id
ON mes_core.state_log(state_id);

CREATE INDEX idx_state_log_state_type_id
ON mes_core.state_log(state_type_id);

-- Trigger Functions: state_log

CREATE OR REPLACE FUNCTION trgfn_set_from_state_id()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT state_id
    INTO NEW.from_state_id
    FROM mes_core.state_log
    WHERE asset_id = NEW.asset_id
    ORDER BY logged_at DESC
    LIMIT 1;

    IF NOT FOUND THEN
        NEW.from_state_id := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;

CREATE TRIGGER trg_state_log_from_state
BEFORE INSERT ON mes_core.state_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_set_from_state_id();

CREATE OR REPLACE FUNCTION trgfn_state_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT sd.state_name, st.state_type_name
    INTO NEW.state_name, NEW.state_type_name
    FROM mes_core.state_definition sd
    INNER JOIN mes_core.state_type st ON sd.state_type_id = st.state_type_id
    WHERE sd.state_id = NEW.state_id;

    IF NEW.downtime_reason_id IS NOT NULL THEN
        SELECT downtime_reason_code, downtime_reason_name
        INTO NEW.downtime_reason_code, NEW.downtime_reason_name
        FROM mes_core.downtime_reason
        WHERE downtime_reason_id = NEW.downtime_reason_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;

CREATE TRIGGER trg_state_log_populate_descriptives
BEFORE INSERT ON mes_core.state_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_state_log_populate_descriptives();

CREATE TRIGGER trg_state_log_updated_at
BEFORE UPDATE ON mes_core.state_log
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

-- ===============================================================
-- Table: state_log_note
-- Description: Notes linked to StateLog entries
-- ===============================================================

CREATE TABLE state_log_note (
    note_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    state_log_id  BIGINT NOT NULL,
    note          TEXT NOT NULL,
    created_by    TEXT DEFAULT CURRENT_USER,
    created_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by    TEXT,
    updated_at    TIMESTAMPTZ,
    removed       BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.state_log_note IS E'@omit delete
Notes linked to state log entries. Can be created, read, and updated via GraphQL API. Use soft delete (set removed=true) instead of hard delete.';

CREATE INDEX idx_state_log_note_state_log_id
ON mes_core.state_log_note(state_log_id);

CREATE TRIGGER trg_validate_state_log_fk
BEFORE INSERT OR UPDATE ON mes_core.state_log_note
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('state_log', 'state_log_id');

CREATE TRIGGER trg_state_log_note_updated_at
BEFORE UPDATE ON mes_core.state_log_note
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_state_log_note
AFTER INSERT OR UPDATE OR DELETE ON mes_core.state_log_note
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: production_log
-- Description: Logs production runs by asset and product
-- ===============================================================

CREATE TABLE production_log (
    production_log_id   BIGINT GENERATED ALWAYS AS IDENTITY,
    asset_id            BIGINT NOT NULL REFERENCES asset_definition(asset_id),
    asset_name          TEXT NOT NULL,
    product_id          BIGINT NOT NULL REFERENCES product_definition(product_id),
    product_name        TEXT NOT NULL,
    product_family_id   BIGINT NOT NULL REFERENCES product_family(product_family_id),
    product_family_name TEXT NOT NULL,
    start_ts            TIMESTAMPTZ NOT NULL,
    end_ts              TIMESTAMPTZ,
    additional_info     JSONB,
    logged_by           TEXT DEFAULT CURRENT_USER,
    logged_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by          TEXT,
    updated_at          TIMESTAMPTZ,
    removed             BOOLEAN DEFAULT FALSE
);

-- Production Log Comments
COMMENT ON TABLE mes_core.production_log IS E'@omit delete
Logs production runs, tracking start and end times for assets. Records can be updated but not deleted via GraphQL API (use soft delete with removed=true).';
COMMENT ON COLUMN mes_core.production_log.production_log_id IS 'Surrogate identity for the production_log record.';
COMMENT ON COLUMN mes_core.production_log.asset_id IS 'Reference to the asset executing the production run.';
COMMENT ON COLUMN mes_core.production_log.asset_name IS 'Snapshot of the asset name at the time of production.';
COMMENT ON COLUMN mes_core.production_log.product_id IS 'FK to the product being manufactured.';
COMMENT ON COLUMN mes_core.production_log.product_name IS 'Snapshot of the product name at the time of run.';
COMMENT ON COLUMN mes_core.production_log.product_family_id IS 'FK to the product family the product belongs to.';
COMMENT ON COLUMN mes_core.production_log.product_family_name IS 'Snapshot of the product family name.';
COMMENT ON COLUMN mes_core.production_log.start_ts IS 'Timestamp marking the start of the production run.';
COMMENT ON COLUMN mes_core.production_log.end_ts IS 'Timestamp marking the end of the production run.';
COMMENT ON COLUMN mes_core.production_log.additional_info IS 'Additional structured metadata such as shift code, lot number, or runtime context.';
COMMENT ON COLUMN mes_core.production_log.logged_by IS 'User or system who recorded the run.';
COMMENT ON COLUMN mes_core.production_log.logged_at IS 'Timestamp when the run was logged.';
COMMENT ON COLUMN mes_core.production_log.updated_by IS 'User who last updated this run.';
COMMENT ON COLUMN mes_core.production_log.updated_at IS 'Timestamp of last modification.';
COMMENT ON COLUMN mes_core.production_log.removed IS 'TRUE if the row is soft-deleted.';

CREATE INDEX idx_production_log_asset_time
ON mes_core.production_log(asset_id, start_ts);

CREATE INDEX idx_production_log_product_id
ON mes_core.production_log(product_id);

CREATE INDEX idx_production_log_product_family_id
ON mes_core.production_log(product_family_id);

-- Trigger Functions: production_log

CREATE OR REPLACE FUNCTION trgfn_production_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT product_name
    INTO NEW.product_name
    FROM mes_core.product_definition
    WHERE product_id = NEW.product_id;

    SELECT product_family_name
    INTO NEW.product_family_name
    FROM mes_core.product_family
    WHERE product_family_id = NEW.product_family_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;

CREATE TRIGGER trg_production_log_populate_descriptives
BEFORE INSERT ON mes_core.production_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_production_log_populate_descriptives();

CREATE TRIGGER trg_production_log_updated_at
BEFORE UPDATE ON mes_core.production_log
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

-- ===============================================================
-- Table: production_log_note
-- Description: Notes linked to ProductionLog entries
-- ===============================================================

CREATE TABLE production_log_note (
    note_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    production_log_id  BIGINT NOT NULL,
    note               TEXT NOT NULL,
    created_by         TEXT DEFAULT CURRENT_USER,
    created_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by         TEXT,
    updated_at         TIMESTAMPTZ,
    removed            BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.production_log_note IS E'@omit delete
Notes linked to production log entries. Can be created, read, and updated via GraphQL API. Use soft delete (set removed=true) instead of hard delete.';

CREATE INDEX idx_production_log_note_production_log_id
ON mes_core.production_log_note(production_log_id);

CREATE TRIGGER trg_validate_production_log_fk
BEFORE INSERT OR UPDATE ON mes_core.production_log_note
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('production_log', 'production_log_id');

CREATE TRIGGER trg_production_log_note_updated_at
BEFORE UPDATE ON mes_core.production_log_note
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_production_log_note
AFTER INSERT OR UPDATE OR DELETE ON mes_core.production_log_note
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: count_log
-- Description: Logs count events by type, asset, and product
-- ===============================================================

CREATE TABLE count_log (
    count_log_id        BIGINT GENERATED ALWAYS AS IDENTITY,
    asset_id            BIGINT NOT NULL REFERENCES asset_definition(asset_id),
    asset_name          TEXT NOT NULL,
    production_log_id   BIGINT,
    count_type_id       BIGINT NOT NULL REFERENCES count_type(count_type_id),
    count_type_name     TEXT NOT NULL,
    quantity            NUMERIC(10,2) DEFAULT 0 CHECK (quantity >= 0),
    product_id          BIGINT NOT NULL REFERENCES product_definition(product_id),
    product_name        TEXT NOT NULL,
    product_family_id   BIGINT NOT NULL REFERENCES product_family(product_family_id),
    product_family_name TEXT NOT NULL,
    additional_info     JSONB,
    logged_by           TEXT DEFAULT CURRENT_USER,
    logged_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by          TEXT,
    updated_at          TIMESTAMPTZ,
    removed             BOOLEAN DEFAULT FALSE
);

-- Count Log Comments
COMMENT ON TABLE mes_core.count_log IS E'@omit delete
Logs quantity counts for assets, such as infeed, outfeed, and scrap. Records can be updated but not deleted via GraphQL API (use soft delete with removed=true).';
COMMENT ON COLUMN mes_core.count_log.count_log_id IS 'Surrogate identity for the count_log record.';
COMMENT ON COLUMN mes_core.count_log.asset_id IS 'Reference to the asset that logged the count event.';
COMMENT ON COLUMN mes_core.count_log.asset_name IS 'Snapshot of the asset name at time of count.';
COMMENT ON COLUMN mes_core.count_log.production_log_id IS 'Optional FK to the related production run.';
COMMENT ON COLUMN mes_core.count_log.count_type_id IS 'FK to the type of count (e.g., Infeed, Outfeed, Scrap).';
COMMENT ON COLUMN mes_core.count_log.count_type_name IS 'Snapshot of the count type name.';
COMMENT ON COLUMN mes_core.count_log.quantity IS 'Quantity logged for the event (e.g., units, weight). Must be >= 0.';
COMMENT ON COLUMN mes_core.count_log.product_id IS 'FK to the product associated with the count.';
COMMENT ON COLUMN mes_core.count_log.product_name IS 'Snapshot of the product name at the time of logging.';
COMMENT ON COLUMN mes_core.count_log.product_family_id IS 'FK to the product family.';
COMMENT ON COLUMN mes_core.count_log.product_family_name IS 'Snapshot of the product family name.';
COMMENT ON COLUMN mes_core.count_log.additional_info IS 'Structured metadata such as measurement source or calculation context.';
COMMENT ON COLUMN mes_core.count_log.logged_by IS 'User or process that logged the count event.';
COMMENT ON COLUMN mes_core.count_log.logged_at IS 'Timestamp when the count was recorded.';
COMMENT ON COLUMN mes_core.count_log.updated_by IS 'User who last modified the record.';
COMMENT ON COLUMN mes_core.count_log.updated_at IS 'Timestamp of last update.';
COMMENT ON COLUMN mes_core.count_log.removed IS 'TRUE if this row has been soft-deleted.';

CREATE INDEX idx_count_log_product_id
ON mes_core.count_log(product_id);

CREATE INDEX idx_count_log_production_log_id_logged_at
ON mes_core.count_log(production_log_id, logged_at);

-- Trigger Functions: count_log

CREATE OR REPLACE FUNCTION trgfn_count_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT count_type_name
    INTO NEW.count_type_name
    FROM mes_core.count_type
    WHERE count_type_id = NEW.count_type_id;

    SELECT product_name
    INTO NEW.product_name
    FROM mes_core.product_definition
    WHERE product_id = NEW.product_id;

    SELECT product_family_name
    INTO NEW.product_family_name
    FROM mes_core.product_family
    WHERE product_family_id = NEW.product_family_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;

CREATE TRIGGER trg_count_log_populate_descriptives
BEFORE INSERT ON mes_core.count_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_count_log_populate_descriptives();

CREATE TRIGGER trg_validate_count_log_fk
BEFORE INSERT OR UPDATE ON mes_core.count_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('production_log', 'production_log_id');

CREATE TRIGGER trg_count_log_updated_at
BEFORE UPDATE ON mes_core.count_log
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

-- ===============================================================
-- Table: count_log_note
-- Description: Notes linked to CountLog entries
-- ===============================================================

CREATE TABLE count_log_note (
    note_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    count_log_id   BIGINT NOT NULL,
    note           TEXT NOT NULL,
    created_by     TEXT DEFAULT CURRENT_USER,
    created_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by     TEXT,
    updated_at     TIMESTAMPTZ,
    removed        BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.count_log_note IS E'@omit delete
Notes linked to count log entries. Can be created, read, and updated via GraphQL API. Use soft delete (set removed=true) instead of hard delete.';

CREATE INDEX idx_count_log_note_count_log_id
ON mes_core.count_log_note(count_log_id);

CREATE TRIGGER trg_validate_count_log_note_fk
BEFORE INSERT OR UPDATE ON mes_core.count_log_note
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('count_log', 'count_log_id');

CREATE TRIGGER trg_count_log_note_updated_at
BEFORE UPDATE ON mes_core.count_log_note
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_count_log_note
AFTER INSERT OR UPDATE OR DELETE ON mes_core.count_log_note
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: measurement_log
-- Description: Logs product measurements by asset and type
-- ===============================================================

CREATE TABLE measurement_log (
    measurement_log_id        BIGINT GENERATED ALWAYS AS IDENTITY,
    asset_id              BIGINT NOT NULL REFERENCES asset_definition(asset_id),
    asset_name            TEXT NOT NULL,
    product_id            BIGINT REFERENCES product_definition(product_id),
    product_name          TEXT,
    product_family_id   BIGINT NOT NULL REFERENCES product_family(product_family_id),
    product_family_name TEXT NOT NULL,
    measurement_type_id   BIGINT NOT NULL REFERENCES measurement_type(measurement_type_id),
    measurement_type_name TEXT NOT NULL,
    target_value          NUMERIC(10,2),
    actual_value          NUMERIC(10,2),
    unit_of_measure       TEXT,
    tolerance             NUMERIC(5,4) DEFAULT 0 CHECK (tolerance >= 0),
    in_tolerance          BOOLEAN,
    additional_info       JSONB,
    logged_by             TEXT DEFAULT CURRENT_USER,
    logged_at             TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by            TEXT,
    updated_at            TIMESTAMPTZ,
    removed               BOOLEAN DEFAULT FALSE
);

-- Measurement Log Comments
COMMENT ON TABLE mes_core.measurement_log IS E'@omit delete
Logs measurements or inspections for produced items. Records can be updated but not deleted via GraphQL API (use soft delete with removed=true).';
COMMENT ON COLUMN mes_core.measurement_log.measurement_log_id IS 'Surrogate identity for the measurement_log record.';
COMMENT ON COLUMN mes_core.measurement_log.asset_id IS 'Reference to the asset where the measurement occurred.';
COMMENT ON COLUMN mes_core.measurement_log.asset_name IS 'Snapshot of the asset name at the time of measurement.';
COMMENT ON COLUMN mes_core.measurement_log.product_id IS 'Optional FK to the product being measured.';
COMMENT ON COLUMN mes_core.measurement_log.product_name IS 'Snapshot of the product name.';
COMMENT ON COLUMN mes_core.measurement_log.product_family_id IS 'FK to the family of the product.';
COMMENT ON COLUMN mes_core.measurement_log.product_family_name IS 'Snapshot of the product family name.';
COMMENT ON COLUMN mes_core.measurement_log.measurement_type_id IS 'FK to the type of measurement (e.g., Weight, pH).';
COMMENT ON COLUMN mes_core.measurement_log.measurement_type_name IS 'Snapshot of the measurement type name.';
COMMENT ON COLUMN mes_core.measurement_log.target_value IS 'Expected or target value for the measurement.';
COMMENT ON COLUMN mes_core.measurement_log.actual_value IS 'Actual recorded measurement value.';
COMMENT ON COLUMN mes_core.measurement_log.unit_of_measure IS 'Measurement unit (e.g., grams, mm).';
COMMENT ON COLUMN mes_core.measurement_log.tolerance IS 'Acceptable deviation from the target value.';
COMMENT ON COLUMN mes_core.measurement_log.in_tolerance IS 'TRUE if the actual value was within tolerance limits.';
COMMENT ON COLUMN mes_core.measurement_log.additional_info IS 'Structured metadata describing measurement context, conditions, or tooling.';
COMMENT ON COLUMN mes_core.measurement_log.logged_by IS 'User or device that logged the measurement.';
COMMENT ON COLUMN mes_core.measurement_log.logged_at IS 'Timestamp when the measurement was recorded.';
COMMENT ON COLUMN mes_core.measurement_log.updated_by IS 'User who last updated the record.';
COMMENT ON COLUMN mes_core.measurement_log.updated_at IS 'Timestamp of last modification.';
COMMENT ON COLUMN mes_core.measurement_log.removed IS 'TRUE if this record is soft-deleted.';

CREATE INDEX idx_measurement_log_asset_product_measurement_type
ON mes_core.measurement_log(asset_id, product_id, measurement_type_id, logged_at);

CREATE INDEX idx_measurement_log_product_measurement_type
ON mes_core.measurement_log(product_id, measurement_type_id);

-- Trigger Functions: measurement_log

CREATE OR REPLACE FUNCTION trgfn_measurement_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT measurement_type_name
    INTO NEW.measurement_type_name
    FROM mes_core.measurement_type
    WHERE measurement_type_id = NEW.measurement_type_id;

    IF NEW.product_id IS NOT NULL THEN
        SELECT product_name
        INTO NEW.product_name
        FROM mes_core.product_definition
        WHERE product_id = NEW.product_id;
    END IF;

    SELECT product_family_name
    INTO NEW.product_family_name
    FROM mes_core.product_family
    WHERE product_family_id = NEW.product_family_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;

CREATE TRIGGER trg_measurement_log_populate_descriptives
BEFORE INSERT ON mes_core.measurement_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_measurement_log_populate_descriptives();

CREATE TRIGGER trg_measurement_log_updated_at
BEFORE UPDATE ON mes_core.measurement_log
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

-- ===============================================================
-- Table: measurement_log_note
-- Description: Notes linked to MeasurementLog entries
-- ===============================================================

CREATE TABLE measurement_log_note (
    note_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    measurement_log_id  BIGINT NOT NULL,
    note            TEXT NOT NULL,
    created_by      TEXT DEFAULT CURRENT_USER,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by      TEXT,
    updated_at      TIMESTAMPTZ,
    removed         BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.measurement_log_note IS E'@omit delete
Notes linked to measurement log entries. Can be created, read, and updated via GraphQL API. Use soft delete (set removed=true) instead of hard delete.';

CREATE INDEX idx_measurement_log_note_measurement_log_id
ON mes_core.measurement_log_note(measurement_log_id);

CREATE TRIGGER trg_validate_measurement_log_fk
BEFORE INSERT OR UPDATE ON mes_core.measurement_log_note
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('measurement_log', 'measurement_log_id');

CREATE TRIGGER trg_measurement_log_note_updated_at
BEFORE UPDATE ON mes_core.measurement_log_note
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_measurement_log_note
AFTER INSERT OR UPDATE OR DELETE ON mes_core.measurement_log_note
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: kpi_log
-- Description: Logs KPI metrics over time windows
-- ===============================================================

CREATE TABLE kpi_log (
    kpi_log_id     BIGINT GENERATED ALWAYS AS IDENTITY,
    asset_id       BIGINT NOT NULL REFERENCES asset_definition(asset_id),
    asset_name     TEXT NOT NULL,
    kpi_id         BIGINT NOT NULL REFERENCES kpi_definition(kpi_id),
    kpi_name       TEXT NOT NULL,
    kpi_value      NUMERIC(10,2) NOT NULL,
    start_ts       TIMESTAMPTZ NOT NULL,
    end_ts         TIMESTAMPTZ NOT NULL,
    additional_info JSONB,
    logged_by      TEXT DEFAULT CURRENT_USER,
    logged_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by     TEXT,
    updated_at     TIMESTAMPTZ,
    removed        BOOLEAN DEFAULT FALSE
);

-- KPI Log Comments
COMMENT ON TABLE mes_core.kpi_log IS E'@omit delete
Logs calculated key performance indicators (KPIs) over time for assets. Records can be updated but not deleted via GraphQL API (use soft delete with removed=true).';
COMMENT ON COLUMN mes_core.kpi_log.kpi_log_id IS 'Surrogate identity for the kpi_log record.';
COMMENT ON COLUMN mes_core.kpi_log.asset_id IS 'Reference to the asset the KPI applies to.';
COMMENT ON COLUMN mes_core.kpi_log.asset_name IS 'Snapshot of the asset name for the KPI record.';
COMMENT ON COLUMN mes_core.kpi_log.kpi_id IS 'FK to the KPI definition.';
COMMENT ON COLUMN mes_core.kpi_log.kpi_name IS 'Snapshot of the KPI name.';
COMMENT ON COLUMN mes_core.kpi_log.kpi_value IS 'Calculated KPI value for the defined time range.';
COMMENT ON COLUMN mes_core.kpi_log.start_ts IS 'Start timestamp of the KPI measurement window.';
COMMENT ON COLUMN mes_core.kpi_log.end_ts IS 'End timestamp of the KPI measurement window.';
COMMENT ON COLUMN mes_core.kpi_log.additional_info IS 'Structured metadata explaining KPI context or parameters.';
COMMENT ON COLUMN mes_core.kpi_log.logged_by IS 'User or process that submitted the KPI record.';
COMMENT ON COLUMN mes_core.kpi_log.logged_at IS 'Timestamp when the KPI record was created.';
COMMENT ON COLUMN mes_core.kpi_log.updated_by IS 'User who last updated the record.';
COMMENT ON COLUMN mes_core.kpi_log.updated_at IS 'Timestamp of last update.';
COMMENT ON COLUMN mes_core.kpi_log.removed IS 'TRUE if this record is soft-deleted.';


CREATE INDEX idx_kpi_log_asset_kpi_id_time
ON mes_core.kpi_log(asset_id, kpi_id, start_ts);

-- Trigger Functions: kpi_log

CREATE OR REPLACE FUNCTION trgfn_kpi_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT kpi_name
    INTO NEW.kpi_name
    FROM mes_core.kpi_definition
    WHERE kpi_id = NEW.kpi_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;

CREATE TRIGGER trg_kpi_log_populate_descriptives
BEFORE INSERT ON mes_core.kpi_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_kpi_log_populate_descriptives();

CREATE TRIGGER trg_kpi_log_updated_at
BEFORE UPDATE ON mes_core.kpi_log
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

-- ===============================================================
-- Table: kpi_log_note
-- Description: Notes linked to KpiLog entries
-- ===============================================================

CREATE TABLE kpi_log_note (
    note_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kpi_log_id   BIGINT NOT NULL,
    note         TEXT NOT NULL,
    created_by   TEXT DEFAULT CURRENT_USER,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by   TEXT,
    updated_at   TIMESTAMPTZ,
    removed      BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.kpi_log_note IS E'@omit delete
Notes linked to KPI log entries. Can be created, read, and updated via GraphQL API. Use soft delete (set removed=true) instead of hard delete.';

CREATE INDEX idx_kpi_log_note_kpi_log_id
ON mes_core.kpi_log_note(kpi_log_id);

CREATE TRIGGER trg_validate_kpi_log_fk
BEFORE INSERT OR UPDATE ON mes_core.kpi_log_note
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('kpi_log', 'kpi_log_id');

CREATE TRIGGER trg_kpi_log_note_updated_at
BEFORE UPDATE ON mes_core.kpi_log_note
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_kpi_log_note
AFTER INSERT OR UPDATE OR DELETE ON mes_core.kpi_log_note
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: general_note
-- Description: Standalone notes not linked to specific logs
-- ===============================================================

CREATE TABLE general_note (
    note_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note        TEXT NOT NULL,
    created_by  TEXT DEFAULT CURRENT_USER,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by  TEXT,
    updated_at  TIMESTAMPTZ,
    removed     BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.general_note IS E'@omit delete
Standalone notes not linked to specific logs. Can be created, read, and updated via GraphQL API. Use soft delete (set removed=true) instead of hard delete.';

CREATE TRIGGER trg_general_note_updated_at
BEFORE UPDATE ON general_note
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_general_note
AFTER INSERT OR UPDATE OR DELETE ON general_note
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();
