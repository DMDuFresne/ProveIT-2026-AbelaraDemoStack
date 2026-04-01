-- ============================================================================
-- 13. ASSET DEFINITIONS - Sites 2 & 3 (Equipment Hierarchy)
-- Run Order: 13 (requires 01-asset-types.sql, 10-asset-definitions.sql)
-- Adds full ISA-95 hierarchy for Site 2 (Filler Central) and
-- Site 3 (Riverside Distribution Center)
-- Note: No unique constraint on (asset_name, parent_asset_id) — avoid re-running
-- ============================================================================

DO $$
DECLARE
    -- Asset Type IDs (looked up by name)
    v_type_area BIGINT;
    v_type_line BIGINT;
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

    -- Existing Sites (looked up from 10-asset-definitions.sql)
    v_site2 BIGINT;
    v_site3 BIGINT;

    -- ========================================================================
    -- Site 2 variables
    -- ========================================================================
    -- Level 3: Areas
    v_s2_filler_production BIGINT;
    v_s2_liquid_processing BIGINT;
    v_s2_packaging BIGINT;
    v_s2_palletizing BIGINT;

    -- Level 4: Lines - Filler Production
    v_s2_filling_line01 BIGINT;
    v_s2_filling_line02 BIGINT;

    -- Level 4: Lines - Liquid Processing
    v_s2_mix_room01 BIGINT;
    v_s2_tank_storage01 BIGINT;

    -- Level 4: Lines - Packaging
    v_s2_labeler_line01 BIGINT;
    v_s2_labeler_line02 BIGINT;

    -- Level 4: Lines - Palletizing
    v_s2_palletizer01 BIGINT;
    v_s2_palletizer_manual01 BIGINT;
    v_s2_palletizer_manual02 BIGINT;

    -- ========================================================================
    -- Site 3 variables
    -- ========================================================================
    -- Level 3: Areas
    v_s3_filler_production BIGINT;
    v_s3_liquid_processing BIGINT;
    v_s3_packaging BIGINT;
    v_s3_palletizing BIGINT;

    -- Level 4: Lines
    v_s3_filling_line01 BIGINT;
    v_s3_mix_room01 BIGINT;
    v_s3_tank_storage01 BIGINT;
    v_s3_labeler_line01 BIGINT;
    v_s3_palletizer_manual01 BIGINT;

BEGIN
    -- ========================================================================
    -- Look up Asset Type IDs by name
    -- ========================================================================
    SELECT asset_type_id INTO v_type_area FROM mes_core.asset_type WHERE asset_type_name = 'Area';
    SELECT asset_type_id INTO v_type_line FROM mes_core.asset_type WHERE asset_type_name = 'Line';
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
    -- Look up existing Site records (created by 10-asset-definitions.sql)
    -- ========================================================================
    SELECT asset_id INTO v_site2 FROM mes_core.asset_definition WHERE asset_name = 'Site 2';
    SELECT asset_id INTO v_site3 FROM mes_core.asset_definition WHERE asset_name = 'Site 3';

    IF v_site2 IS NULL THEN
        RAISE EXCEPTION 'Site 2 not found — run 10-asset-definitions.sql first';
    END IF;
    IF v_site3 IS NULL THEN
        RAISE EXCEPTION 'Site 3 not found — run 10-asset-definitions.sql first';
    END IF;

    -- ########################################################################
    --  SITE 2 — Filler Central
    -- ########################################################################

    -- ========================================================================
    -- Level 3: Areas (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Filler Production', 'Production', v_type_area, v_site2, 'Cappy Hour Inc/Site 2/Filler Production', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_filler_production;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Liquid Processing', 'Processing', v_type_area, v_site2, 'Cappy Hour Inc/Site 2/Liquid Processing', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_liquid_processing;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Packaging', 'Labeling, case packing, and sealing', v_type_area, v_site2, 'Cappy Hour Inc/Site 2/Packaging', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_packaging;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Palletizing', 'Pallet loading and stretch wrapping', v_type_area, v_site2, 'Cappy Hour Inc/Site 2/Palletizing', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_palletizing;

    -- ========================================================================
    -- Level 4: Lines — Filler Production (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('FillingLine01', 'Line 1', v_type_line, v_s2_filler_production, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_filling_line01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('FillingLine02', 'Line 2', v_type_line, v_s2_filler_production, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine02', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_filling_line02;

    -- ========================================================================
    -- Level 4: Lines — Liquid Processing (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('MixRoom01', 'Mix Room', v_type_line, v_s2_liquid_processing, 'Cappy Hour Inc/Site 2/Liquid Processing/MixRoom01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_mix_room01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('TankStorage01', 'Central Tanks', v_type_line, v_s2_liquid_processing, 'Cappy Hour Inc/Site 2/Liquid Processing/TankStorage01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_tank_storage01;

    -- ========================================================================
    -- Level 4: Lines — Packaging (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('LabelerLine01', 'Labeler Left', v_type_line, v_s2_packaging, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_labeler_line01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('LabelerLine02', 'Labeler Right', v_type_line, v_s2_packaging, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine02', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_labeler_line02;

    -- ========================================================================
    -- Level 4: Lines — Palletizing (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Palletizer01', 'Palletizer', v_type_line, v_s2_palletizing, 'Cappy Hour Inc/Site 2/Palletizing/Palletizer01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_palletizer01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('PalletizerManual01', 'Left Station', v_type_line, v_s2_palletizing, 'Cappy Hour Inc/Site 2/Palletizing/PalletizerManual01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_palletizer_manual01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('PalletizerManual02', 'Right Station', v_type_line, v_s2_palletizing, 'Cappy Hour Inc/Site 2/Palletizing/PalletizerManual02', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s2_palletizer_manual02;

    -- ========================================================================
    -- Level 5: Work Centers — FillingLine01 (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Filler', 'Filler', v_type_filler, v_s2_filling_line01, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine01/Filler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('CapLoader', 'CapLoader', v_type_caploader, v_s2_filling_line01, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine01/CapLoader', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Washer', 'Washer', v_type_washer, v_s2_filling_line01, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine01/Washer', 'seed', NOW(), 'seed', NOW(), false);

    -- Level 5: Work Centers — FillingLine02 (Site 2)
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Filler', 'Filler', v_type_filler, v_s2_filling_line02, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine02/Filler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('CapLoader', 'Line 2', v_type_caploader, v_s2_filling_line02, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine02/CapLoader', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Washer', 'Washer', v_type_washer, v_s2_filling_line02, 'Cappy Hour Inc/Site 2/Filler Production/FillingLine02/Washer', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — MixRoom01 (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Vat01', 'Vat01', v_type_vat, v_s2_mix_room01, 'Cappy Hour Inc/Site 2/Liquid Processing/MixRoom01/Vat01', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Vat02', 'North Vat', v_type_vat, v_s2_mix_room01, 'Cappy Hour Inc/Site 2/Liquid Processing/MixRoom01/Vat02', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — TankStorage01 (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank01', 'Left Tank', v_type_tank, v_s2_tank_storage01, 'Cappy Hour Inc/Site 2/Liquid Processing/TankStorage01/Tank01', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank02', 'Tank02', v_type_tank, v_s2_tank_storage01, 'Cappy Hour Inc/Site 2/Liquid Processing/TankStorage01/Tank02', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank03', 'Tank03', v_type_tank, v_s2_tank_storage01, 'Cappy Hour Inc/Site 2/Liquid Processing/TankStorage01/Tank03', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — LabelerLine01 (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Labeler', 'Labeler', v_type_labeler, v_s2_labeler_line01, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine01/Labeler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Packager', 'Packager', v_type_packager, v_s2_labeler_line01, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine01/Packager', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Sealer', 'Sealer', v_type_sealer, v_s2_labeler_line01, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine01/Sealer', 'seed', NOW(), 'seed', NOW(), false);

    -- Level 5: Work Centers — LabelerLine02 (Site 2)
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Labeler', 'Labeler', v_type_labeler, v_s2_labeler_line02, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine02/Labeler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Packager', 'Packager', v_type_packager, v_s2_labeler_line02, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine02/Packager', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Sealer', 'Sealer', v_type_sealer, v_s2_labeler_line02, 'Cappy Hour Inc/Site 2/Packaging/LabelerLine02/Sealer', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — Palletizer01 (Site 2)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Pallet01', 'Pallet01', v_type_palletstation, v_s2_palletizer01, 'Cappy Hour Inc/Site 2/Palletizing/Palletizer01/Pallet01', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Pallet02', 'West Pallet', v_type_palletstation, v_s2_palletizer01, 'Cappy Hour Inc/Site 2/Palletizing/Palletizer01/Pallet02', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Robot', 'Robot', v_type_robot, v_s2_palletizer01, 'Cappy Hour Inc/Site 2/Palletizing/Palletizer01/Robot', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Wrapper', 'Wrapper', v_type_wrapper, v_s2_palletizer01, 'Cappy Hour Inc/Site 2/Palletizing/Palletizer01/Wrapper', 'seed', NOW(), 'seed', NOW(), false);

    -- Level 5: Work Centers — PalletizerManual01 (Site 2)
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Workstation01', 'Manual Stacker', v_type_workstation, v_s2_palletizer_manual01, 'Cappy Hour Inc/Site 2/Palletizing/PalletizerManual01/Workstation01', 'seed', NOW(), 'seed', NOW(), false);

    -- Level 5: Work Centers — PalletizerManual02 (Site 2)
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Workstation01', 'Right Station', v_type_workstation, v_s2_palletizer_manual02, 'Cappy Hour Inc/Site 2/Palletizing/PalletizerManual02/Workstation01', 'seed', NOW(), 'seed', NOW(), false);

    -- ########################################################################
    --  SITE 3 — Riverside Distribution Center
    -- ########################################################################

    -- ========================================================================
    -- Level 3: Areas (Site 3)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Filler Production', 'Production', v_type_area, v_site3, 'Cappy Hour Inc/Site 3/Filler Production', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_filler_production;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Liquid Processing', 'Processing', v_type_area, v_site3, 'Cappy Hour Inc/Site 3/Liquid Processing', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_liquid_processing;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Packaging', 'Packaging', v_type_area, v_site3, 'Cappy Hour Inc/Site 3/Packaging', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_packaging;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('Palletizing', 'Palletizing', v_type_area, v_site3, 'Cappy Hour Inc/Site 3/Palletizing', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_palletizing;

    -- ========================================================================
    -- Level 4: Lines (Site 3)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('FillingLine01', 'Filling', v_type_line, v_s3_filler_production, 'Cappy Hour Inc/Site 3/Filler Production/FillingLine01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_filling_line01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('MixRoom01', 'Mix Room', v_type_line, v_s3_liquid_processing, 'Cappy Hour Inc/Site 3/Liquid Processing/MixRoom01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_mix_room01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('TankStorage01', 'TankStorage01', v_type_line, v_s3_liquid_processing, 'Cappy Hour Inc/Site 3/Liquid Processing/TankStorage01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_tank_storage01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('LabelerLine01', 'LabelerLine01', v_type_line, v_s3_packaging, 'Cappy Hour Inc/Site 3/Packaging/LabelerLine01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_labeler_line01;

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed)
    VALUES ('PalletizerManual01', 'Stacker', v_type_line, v_s3_palletizing, 'Cappy Hour Inc/Site 3/Palletizing/PalletizerManual01', 'seed', NOW(), 'seed', NOW(), false)
    RETURNING asset_id INTO v_s3_palletizer_manual01;

    -- ========================================================================
    -- Level 5: Work Centers — FillingLine01 (Site 3)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Filler', 'Filler', v_type_filler, v_s3_filling_line01, 'Cappy Hour Inc/Site 3/Filler Production/FillingLine01/Filler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('CapLoader', 'Cap Loader', v_type_caploader, v_s3_filling_line01, 'Cappy Hour Inc/Site 3/Filler Production/FillingLine01/CapLoader', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Washer', 'Washer', v_type_washer, v_s3_filling_line01, 'Cappy Hour Inc/Site 3/Filler Production/FillingLine01/Washer', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — MixRoom01 (Site 3)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Vat01', 'Vat', v_type_vat, v_s3_mix_room01, 'Cappy Hour Inc/Site 3/Liquid Processing/MixRoom01/Vat01', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — TankStorage01 (Site 3)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank01', 'North Tank', v_type_tank, v_s3_tank_storage01, 'Cappy Hour Inc/Site 3/Liquid Processing/TankStorage01/Tank01', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Tank02', 'South Tank', v_type_tank, v_s3_tank_storage01, 'Cappy Hour Inc/Site 3/Liquid Processing/TankStorage01/Tank02', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — LabelerLine01 (Site 3)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Labeler', 'Labeler', v_type_labeler, v_s3_labeler_line01, 'Cappy Hour Inc/Site 3/Packaging/LabelerLine01/Labeler', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Packager', 'Packager', v_type_packager, v_s3_labeler_line01, 'Cappy Hour Inc/Site 3/Packaging/LabelerLine01/Packager', 'seed', NOW(), 'seed', NOW(), false);

    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Sealer', 'Sealer', v_type_sealer, v_s3_labeler_line01, 'Cappy Hour Inc/Site 3/Packaging/LabelerLine01/Sealer', 'seed', NOW(), 'seed', NOW(), false);

    -- ========================================================================
    -- Level 5: Work Centers — PalletizerManual01 (Site 3)
    -- ========================================================================
    INSERT INTO mes_core.asset_definition (asset_name, asset_description, asset_type_id, parent_asset_id, tag_path, created_by, created_at, updated_by, updated_at, removed) VALUES
    ('Workstation01', 'Stacker', v_type_workstation, v_s3_palletizer_manual01, 'Cappy Hour Inc/Site 3/Palletizing/PalletizerManual01/Workstation01', 'seed', NOW(), 'seed', NOW(), false);

    RAISE NOTICE 'Sites 2 & 3 asset hierarchy seeded successfully';
END $$;
