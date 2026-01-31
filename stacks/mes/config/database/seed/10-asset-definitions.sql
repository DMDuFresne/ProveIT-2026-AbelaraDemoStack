-- ============================================================================
-- 10. ASSET DEFINITIONS (Equipment Hierarchy)
-- Run Order: 10 of 10 (requires 01-asset-types.sql)
-- Full ISA-95 asset hierarchy for Cappy Hour Inc
-- Note: No unique constraint on tag_path - run on fresh database only
-- ============================================================================

DO $$
DECLARE
    -- Asset Type IDs (looked up by name)
    v_type_enterprise BIGINT;
    v_type_site BIGINT;
    v_type_area BIGINT;
    v_type_line BIGINT;
    -- Legacy types (kept for reference)
    v_type_workcenter BIGINT;
    v_type_equipment BIGINT;
    -- Specific Work Center Types
    v_type_filler BIGINT;
    v_type_caploader BIGINT;
    v_type_washer BIGINT;
    v_type_labeler BIGINT;
    v_type_packager BIGINT;
    v_type_sealer BIGINT;
    -- Specific Equipment Types
    v_type_tank BIGINT;
    v_type_vat BIGINT;
    v_type_palletstation BIGINT;
    v_type_robot BIGINT;
    v_type_wrapper BIGINT;
    v_type_workstation BIGINT;

    -- Level 1: Enterprise
    v_enterprise BIGINT;

    -- Level 2: Sites
    v_plant1 BIGINT;
    v_plant2 BIGINT;
    v_plant3 BIGINT;

    -- Level 3: Areas (Plant1)
    v_filler_production BIGINT;
    v_liquid_processing BIGINT;
    v_packaging BIGINT;
    v_palletizing BIGINT;

    -- Level 4: Lines - FillerProduction
    v_filling_line01 BIGINT;
    v_filling_line02 BIGINT;
    v_filling_line03 BIGINT;

    -- Level 4: Lines - LiquidProcessing
    v_mix_room01 BIGINT;
    v_tank_storage01 BIGINT;

    -- Level 4: Lines - Packaging
    v_labeler_line01 BIGINT;
    v_labeler_line02 BIGINT;
    v_labeler_line03 BIGINT;
    v_labeler_line04 BIGINT;

    -- Level 4: Lines - Palletizing
    v_palletizer01 BIGINT;
    v_palletizer02 BIGINT;
    v_palletizer_manual01 BIGINT;
    v_palletizer_manual02 BIGINT;
    v_palletizer_manual03 BIGINT;
    v_palletizer_manual04 BIGINT;

BEGIN
    -- ========================================================================
    -- Look up Asset Type IDs by name
    -- ========================================================================
    -- Hierarchy types
    SELECT asset_type_id INTO v_type_enterprise FROM mes_core.asset_type WHERE asset_type_name = 'Enterprise';
    SELECT asset_type_id INTO v_type_site FROM mes_core.asset_type WHERE asset_type_name = 'Site';
    SELECT asset_type_id INTO v_type_area FROM mes_core.asset_type WHERE asset_type_name = 'Area';
    SELECT asset_type_id INTO v_type_line FROM mes_core.asset_type WHERE asset_type_name = 'Line';
    -- Legacy types (kept for reference)
    SELECT asset_type_id INTO v_type_workcenter FROM mes_core.asset_type WHERE asset_type_name = 'Work Center';
    SELECT asset_type_id INTO v_type_equipment FROM mes_core.asset_type WHERE asset_type_name = 'Equipment';
    -- Specific Work Center Types
    SELECT asset_type_id INTO v_type_filler FROM mes_core.asset_type WHERE asset_type_name = 'Filler';
    SELECT asset_type_id INTO v_type_caploader FROM mes_core.asset_type WHERE asset_type_name = 'CapLoader';
    SELECT asset_type_id INTO v_type_washer FROM mes_core.asset_type WHERE asset_type_name = 'Washer';
    SELECT asset_type_id INTO v_type_labeler FROM mes_core.asset_type WHERE asset_type_name = 'Labeler';
    SELECT asset_type_id INTO v_type_packager FROM mes_core.asset_type WHERE asset_type_name = 'Packager';
    SELECT asset_type_id INTO v_type_sealer FROM mes_core.asset_type WHERE asset_type_name = 'Sealer';
    -- Specific Equipment Types
    SELECT asset_type_id INTO v_type_tank FROM mes_core.asset_type WHERE asset_type_name = 'Tank';
    SELECT asset_type_id INTO v_type_vat FROM mes_core.asset_type WHERE asset_type_name = 'Vat';
    SELECT asset_type_id INTO v_type_palletstation FROM mes_core.asset_type WHERE asset_type_name = 'PalletStation';
    SELECT asset_type_id INTO v_type_robot FROM mes_core.asset_type WHERE asset_type_name = 'Robot';
    SELECT asset_type_id INTO v_type_wrapper FROM mes_core.asset_type WHERE asset_type_name = 'Wrapper';
    SELECT asset_type_id INTO v_type_workstation FROM mes_core.asset_type WHERE asset_type_name = 'Workstation';

    -- ========================================================================
    -- Level 1: Enterprise
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Cappy Hour Inc', 'Cappy Hour Inc.', v_type_enterprise, NULL, 'Cappy Hour Inc', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_enterprise;

    -- ========================================================================
    -- Level 2: Sites
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Site 1', 'The Cap Shack', v_type_site, v_enterprise, 'Cappy Hour Inc/Site 1', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_plant1;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Site 2', 'Filler Central', v_type_site, v_enterprise, 'Cappy Hour Inc/Site 2', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_plant2;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Site 3', 'Site 3', v_type_site, v_enterprise, 'Cappy Hour Inc/Site 3', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_plant3;

    -- ========================================================================
    -- Level 3: Areas (Plant1)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Filler Production', 'Production', v_type_area, v_plant1, 'Cappy Hour Inc/Site 1/Filler Production', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_filler_production;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Liquid Processing', 'Processing', v_type_area, v_plant1, 'Cappy Hour Inc/Site 1/Liquid Processing', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_liquid_processing;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Packaging', 'Packaging', v_type_area, v_plant1, 'Cappy Hour Inc/Site 1/Packaging', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_packaging;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Palletizing', 'Palletizing', v_type_area, v_plant1, 'Cappy Hour Inc/Site 1/Palletizing', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_palletizing;

    -- ========================================================================
    -- Level 4: Lines - FillerProduction
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('FillingLine01', 'Line A', v_type_line, v_filler_production, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_filling_line01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('FillingLine02', 'Line B', v_type_line, v_filler_production, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine02', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_filling_line02;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('FillingLine03', 'High Capacity Line', v_type_line, v_filler_production, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine03', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_filling_line03;

    -- ========================================================================
    -- Level 4: Lines - LiquidProcessing
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('MixRoom01', 'Mix Room', v_type_line, v_liquid_processing, 'Cappy Hour Inc/Site 1/Liquid Processing/MixRoom01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_mix_room01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('TankStorage01', 'North Tanks', v_type_line, v_liquid_processing, 'Cappy Hour Inc/Site 1/Liquid Processing/TankStorage01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_tank_storage01;

    -- ========================================================================
    -- Level 4: Lines - Packaging
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('LabelerLine01', 'Labeler A', v_type_line, v_packaging, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_labeler_line01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('LabelerLine02', 'Labeler B', v_type_line, v_packaging, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine02', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_labeler_line02;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('LabelerLine03', 'Labeler 1', v_type_line, v_packaging, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine03', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_labeler_line03;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('LabelerLine04', 'Labeler 2', v_type_line, v_packaging, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine04', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_labeler_line04;

    -- ========================================================================
    -- Level 4: Lines - Palletizing
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Palletizer01', 'East Robot', v_type_line, v_palletizing, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_palletizer01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Palletizer02', 'West Robot', v_type_line, v_palletizing, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer02', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_palletizer02;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('PalletizerManual01', 'East Robot 1st Stacker', v_type_line, v_palletizing, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_palletizer_manual01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('PalletizerManual02', 'East Robot 2nd Stacker', v_type_line, v_palletizing, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual02', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_palletizer_manual02;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('PalletizerManual03', 'West Robot 1st Stacker', v_type_line, v_palletizing, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual03', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_palletizer_manual03;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('PalletizerManual04', 'West Robot 2nd Stacker', v_type_line, v_palletizing, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual04', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_palletizer_manual04;

    -- ========================================================================
    -- Level 5: Work Centers - FillingLine01
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('CapLoader', 'Capper', v_type_caploader, v_filling_line01, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine01/CapLoader', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Filler', 'Filler', v_type_filler, v_filling_line01, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine01/Filler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Washer', 'Washer', v_type_washer, v_filling_line01, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine01/Washer', 'seed', NOW(), 'seed', NOW(), false);

    -- Level 5: Work Centers - FillingLine02
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Filler', 'Filler', v_type_filler, v_filling_line02, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine02/Filler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('CapLoader', 'Capper', v_type_caploader, v_filling_line02, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine02/CapLoader', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Washer', 'Washer', v_type_washer, v_filling_line02, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine02/Washer', 'seed', NOW(), 'seed', NOW(), false);

    -- Level 5: Work Centers - FillingLine03
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Filler', 'Filler', v_type_filler, v_filling_line03, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine03/Filler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('CapLoader', 'Capper', v_type_caploader, v_filling_line03, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine03/CapLoader', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Washer', 'Washer', v_type_washer, v_filling_line03, 'Cappy Hour Inc/Site 1/Filler Production/FillingLine03/Washer', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers - Packaging (LabelerLine01-04)
    -- ========================================================================
    -- LabelerLine01
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Labeler', 'Labeler', v_type_labeler, v_labeler_line01, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Labeler', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Packager', 'Packager', v_type_packager, v_labeler_line01, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Packager', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Sealer', 'Sealer', v_type_sealer, v_labeler_line01, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine01/Sealer', 'seed', NOW(), 'seed', NOW(), false);

    -- LabelerLine02
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Labeler', 'Labeler', v_type_labeler, v_labeler_line02, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Labeler', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Packager', 'Packager', v_type_packager, v_labeler_line02, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Packager', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Sealer', 'Sealer', v_type_sealer, v_labeler_line02, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine02/Sealer', 'seed', NOW(), 'seed', NOW(), false);

    -- LabelerLine03
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Labeler', 'Labeler', v_type_labeler, v_labeler_line03, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Labeler', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Packager', 'Packager', v_type_packager, v_labeler_line03, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Packager', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Sealer', 'Sealer', v_type_sealer, v_labeler_line03, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine03/Sealer', 'seed', NOW(), 'seed', NOW(), false);

    -- LabelerLine04
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Labeler', 'Labeler', v_type_labeler, v_labeler_line04, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Labeler', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Packager', 'Packager', v_type_packager, v_labeler_line04, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Packager', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Sealer', 'Sealer', v_type_sealer, v_labeler_line04, 'Cappy Hour Inc/Site 1/Packaging/LabelerLine04/Sealer', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 6: Equipment - Vats (MixRoom01)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Vat01', 'Jeff', v_type_vat, v_mix_room01, 'Cappy Hour Inc/Site 1/Liquid Processing/MixRoom01/Vat01', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Vat02', 'Raymond', v_type_vat, v_mix_room01, 'Cappy Hour Inc/Site 1/Liquid Processing/MixRoom01/Vat02', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Vat03', 'Billy', v_type_vat, v_mix_room01, 'Cappy Hour Inc/Site 1/Liquid Processing/MixRoom01/Vat03', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Vat04', 'Bob', v_type_vat, v_mix_room01, 'Cappy Hour Inc/Site 1/Liquid Processing/MixRoom01/Vat04', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 6: Equipment - Tanks (TankStorage01)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank01', 'Tank 1', v_type_tank, v_tank_storage01, 'Cappy Hour Inc/Site 1/Liquid Processing/TankStorage01/Tank01', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank02', 'Tank 2', v_type_tank, v_tank_storage01, 'Cappy Hour Inc/Site 1/Liquid Processing/TankStorage01/Tank02', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank03', 'Tank 3', v_type_tank, v_tank_storage01, 'Cappy Hour Inc/Site 1/Liquid Processing/TankStorage01/Tank03', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank04', 'Tank 4', v_type_tank, v_tank_storage01, 'Cappy Hour Inc/Site 1/Liquid Processing/TankStorage01/Tank04', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank05', 'Tank 5', v_type_tank, v_tank_storage01, 'Cappy Hour Inc/Site 1/Liquid Processing/TankStorage01/Tank05', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank06', 'Tank 6', v_type_tank, v_tank_storage01, 'Cappy Hour Inc/Site 1/Liquid Processing/TankStorage01/Tank06', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 6: Equipment - Palletizer01
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Pallet01', 'East Pallet', v_type_palletstation, v_palletizer01, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer01/Pallet01', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Pallet02', 'West Pallet', v_type_palletstation, v_palletizer01, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer01/Pallet02', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Robot', 'Robot', v_type_robot, v_palletizer01, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer01/Robot', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Wrapper', 'Wrapper', v_type_wrapper, v_palletizer01, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer01/Wrapper', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 6: Equipment - Palletizer02
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Pallet01', 'East Pallet', v_type_palletstation, v_palletizer02, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer02/Pallet01', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Pallet02', 'West Pallet', v_type_palletstation, v_palletizer02, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer02/Pallet02', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Robot', 'Robot', v_type_robot, v_palletizer02, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer02/Robot', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Wrapper', 'Wrapper', v_type_wrapper, v_palletizer02, 'Cappy Hour Inc/Site 1/Palletizing/Palletizer02/Wrapper', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 6: Equipment - Manual Palletizer Workstations
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Workstation01', 'Manual Stacker', v_type_workstation, v_palletizer_manual01, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual01/Workstation01', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Workstation01', 'Manual Stacker', v_type_workstation, v_palletizer_manual02, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual02/Workstation01', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Workstation01', 'Manual Stacker', v_type_workstation, v_palletizer_manual03, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual03/Workstation01', 'seed', NOW(), 'seed', NOW(), false);
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Workstation01', 'Manual Stacker', v_type_workstation, v_palletizer_manual04, 'Cappy Hour Inc/Site 1/Palletizing/PalletizerManual04/Workstation01', 'seed', NOW(), 'seed', NOW(), false);

END $$;
