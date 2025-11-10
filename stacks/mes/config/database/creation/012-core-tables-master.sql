-- ===============================================================
-- Master Data Tables: mes_core
-- ===============================================================

SET search_path TO mes_core;

-- ===============================================================
-- Table: asset_definition
-- Description: Defines physical or logical assets in the MES
-- ===============================================================

CREATE TABLE asset_definition (
    asset_id          BIGSERIAL PRIMARY KEY,
    asset_name        TEXT NOT NULL,
    asset_description TEXT NOT NULL,
    asset_type_id     BIGINT NOT NULL REFERENCES asset_type(asset_type_id),
    parent_asset_id   BIGINT REFERENCES asset_definition(asset_id) ON DELETE SET NULL,
    tag_path          TEXT,
    created_by        TEXT DEFAULT CURRENT_USER,
    created_at        TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by        TEXT,
    updated_at        TIMESTAMPTZ,
    removed           BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.asset_definition IS E'@omit delete
Defines an asset in the MES system, including its parent-child hierarchy.';
COMMENT ON COLUMN mes_core.asset_definition.asset_name IS 'Human-readable name of the asset.';
COMMENT ON COLUMN mes_core.asset_definition.asset_type_id IS 'Reference to the type of the asset.';
COMMENT ON COLUMN mes_core.asset_definition.parent_asset_id IS 'Reference to the parent asset if part of a hierarchy.';

CREATE INDEX idx_asset_definition_parent_asset_id
ON mes_core.asset_definition(parent_asset_id);

CREATE TRIGGER trg_asset_definition_updated_at
BEFORE UPDATE ON mes_core.asset_definition
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_asset_definition
AFTER INSERT OR UPDATE OR DELETE ON mes_core.asset_definition
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: product_family
-- Description: Defines product families for grouping products
-- ===============================================================

CREATE TABLE product_family (
    product_family_id           BIGSERIAL PRIMARY KEY,
    product_family_name         TEXT UNIQUE NOT NULL,
    product_family_description  TEXT,
    created_by                  TEXT DEFAULT CURRENT_USER,
    created_at                  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by                  TEXT,
    updated_at                  TIMESTAMPTZ,
    removed                     BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.product_family IS E'@omit delete
Groups related products into families for reporting or planning.';
COMMENT ON COLUMN mes_core.product_family.product_family_name IS 'Name of the product family.';

CREATE TRIGGER trg_product_family_updated_at
BEFORE UPDATE ON mes_core.product_family
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_product_family
AFTER INSERT OR UPDATE OR DELETE ON mes_core.product_family
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: product_definition
-- Description: Defines individual products tracked in the MES
-- ===============================================================

CREATE TABLE product_definition (
    product_id           BIGSERIAL PRIMARY KEY,
    product_name         TEXT NOT NULL,
    product_description  TEXT NOT NULL,
    product_family_id    BIGINT REFERENCES product_family(product_family_id),
    unit_of_measure      TEXT DEFAULT 'each',
    tolerance            NUMERIC(5,4) DEFAULT 0 CHECK (tolerance >= 0),
    ideal_cycle_time     NUMERIC(10,2) CHECK (ideal_cycle_time > 0),
    created_by           TEXT DEFAULT CURRENT_USER,
    created_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by           TEXT,
    updated_at           TIMESTAMPTZ,
    removed              BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE mes_core.product_definition IS E'@omit delete
Defines individual products manufactured or processed.';
COMMENT ON COLUMN mes_core.product_definition.product_name IS 'Name of the product.';
COMMENT ON COLUMN mes_core.product_definition.product_family_id IS 'Reference to the associated product family.';
COMMENT ON COLUMN mes_core.product_definition.ideal_cycle_time IS 'Target ideal cycle time (seconds) for the product.';

CREATE INDEX idx_product_definition_product_family_id
ON mes_core.product_definition(product_family_id);

CREATE TRIGGER trg_product_definition_updated_at
BEFORE UPDATE ON mes_core.product_definition
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_product_definition
AFTER INSERT OR UPDATE OR DELETE ON mes_core.product_definition
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();

-- ===============================================================
-- Table: performance_target
-- Description: Defines performance targets per asset and product
-- ===============================================================

CREATE TABLE performance_target (
    product_id       BIGINT NOT NULL REFERENCES product_definition(product_id),
    asset_id         BIGINT NOT NULL REFERENCES asset_definition(asset_id),
    target_value     NUMERIC(10,2) NOT NULL CHECK (target_value > 0),
    target_unit      TEXT,
    created_by       TEXT DEFAULT CURRENT_USER,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by       TEXT,
    updated_at       TIMESTAMPTZ,
    removed          BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (product_id, asset_id)
);

COMMENT ON TABLE mes_core.performance_target IS E'@omit delete
Defines expected performance metrics for a given asset and product.';
COMMENT ON COLUMN mes_core.performance_target.asset_id IS 'Reference to the asset for the target.';
COMMENT ON COLUMN mes_core.performance_target.product_id IS 'Reference to the product for the target.';
COMMENT ON COLUMN mes_core.performance_target.target_value IS 'Expected ideal production rate (units/hour).';

CREATE TRIGGER trg_performance_target_updated_at
BEFORE UPDATE ON mes_core.performance_target
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();

CREATE TRIGGER trg_audit_performance_target
AFTER INSERT OR UPDATE OR DELETE ON mes_core.performance_target
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();
