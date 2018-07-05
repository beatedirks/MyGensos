-- Loading the Energy Model 

-- Keyservices
-- START QUERY --
INSERT INTO "ISL_I_KeyServices" (ks, kstype, supplynw, rc, epi, comfortfactorname, submodel, modelrun_id)
SELECT ks, kstype, supplynw, rc, epi, comfortfactor, submodel, modelrun_id_val
FROM "ISL_LU_KeyServices" WHERE submodel = 'Energy' AND model_schema_id = model_schema_id_val

-- Regions
-- START QUERY --
INSERT INTO "ISL_I_NetworkRegions" (regionname, submodel, modelrun_id) 
SELECT region_id, submodel, modelrun_id_val
FROM "ISL_LU_NetworkRegions" WHERE submodel = 'Energy' AND model_schema_id = model_schema_id_val

-- Generation Assets
-- START QUERY --
-- electricity
INSERT INTO "ISL_I_GenerationAssets" (dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, asset_type, epi, comtype, submodel, cap_ceiling, region, interdep_ids, modelrun_id)
SELECT dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, asset_type, epi, comtype, submodel, cap_ceiling, gor_id, interdep_ids, modelrun_id_val
FROM "EE_IO_GenerationAssetsByGOR" 
WHERE dn = 'Electricity'

-- START QUERY --
-- gas
DO
$do$
BEGIN
--IF (SELECT id FROM "ISL_LU_KeyServices" WHERE supplynw='Gas' AND model_schema_id=model_schema_id_val) > 0 THEN
IF 'Gas' IN (SELECT supplynw FROM "ISL_LU_KeyServices" WHERE model_schema_id=model_schema_id_val) THEN
INSERT INTO "ISL_I_GenerationAssets" (dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, asset_type, epi, comtype, submodel, cap_ceiling, region, interdep_ids, modelrun_id)
SELECT dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, asset_type, epi, comtype, submodel, cap_ceiling, gor_id, interdep_ids, modelrun_id_val
FROM "EE_IO_GenerationAssetsByGOR" 
WHERE dn = 'Gas' AND gor_id IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Energy');
END IF;
END 
$do$


-- Transmission Assets
-- START QUERY --
-- electricity distribution
DO
$do$
BEGIN
IF 'Electricity' IN (SELECT supplynw FROM "ISL_LU_KeyServices" WHERE model_schema_id=model_schema_id_val) THEN
INSERT INTO "ISL_I_NetworkArcs" (cort, dn, origin, destination, submodel, maxcap, instduration, maxlifetime, runcostperunit, instdate, capex, epi, com_type, cap_ceiling, asset_name, modelrun_id)
SELECT 'C', network, origin_id, destination_id, submodel, maxcap, instduration, maxlifetime, runcostperunit, instdate, capex, epi, com_type, cap_ceiling, asset_name, modelrun_id_val
FROM "EE_IO_TransmissionAssetsByGor"
WHERE network = 'Electricity' AND origin_id IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Energy') AND destination_id IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Energy'  AND origin_id <> destination_id);
END IF;
END 
$do$

-- START QUERY --
-- heat dummy transmission arc, necessary to make sure the heat distribution network gets created, even if there is no transmission capacities
DO
$do$
BEGIN
IF 'Heat' IN (SELECT supplynw FROM "ISL_LU_KeyServices" WHERE model_schema_id=model_schema_id_val) THEN
INSERT INTO "ISL_I_NetworkArcs" (cort, dn, origin, destination, submodel, maxcap, instduration, maxlifetime, runcostperunit, instdate, capex, epi, com_type, cap_ceiling, asset_name, modelrun_id)
SELECT 'C','Heat', 9,11, 'Energy', 0, 0, 1000, 0, 2000, 0, 0, 'dummy', 0, 'heat_arc_dummy', modelrun_id_val;
END IF;
END 
$do$

-- START QUERY --
-- gas  pipes
DO
$do$
BEGIN
--IF (SELECT id FROM "ISL_LU_KeyServices" WHERE supplynw='Gas' AND model_schema_id=model_schema_id_val) > 0 THEN
IF 'Gas' IN (SELECT supplynw FROM "ISL_LU_KeyServices" WHERE model_schema_id=model_schema_id_val) THEN
INSERT INTO "ISL_I_NetworkArcs" (cort, dn, origin, destination, submodel, maxcap, instduration, maxlifetime, runcostperunit, instdate, capex, epi, com_type, cap_ceiling, asset_name, modelrun_id)
SELECT 'C', network, origin_id, destination_id, submodel, maxcap, instduration, maxlifetime, runcostperunit, instdate, capex, epi, com_type, cap_ceiling, asset_name, modelrun_id_val
FROM "EE_IO_TransmissionAssetsByGor"
WHERE network = 'Gas' AND origin_id IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Energy') AND destination_id IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Energy' AND origin_id <> destination_id);
END IF;
END 
$do$

-- Interdependencies
-- add Electricity interdependencies to ISL_I_Interdepdencies with values specified in ISL_LU_Interdependencies
-- direct interdepedencies
-- START QUERY --

INSERT INTO "ISL_I_Interdependencies"(intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_name, aff_subm, aff_netw_or_keys, aff_reg1, conversion_factor, modelrun_id)
SELECT 'dir', 'Energy', 'Electricity', 'gen', existingInterdeps.gor_id, existingInterdeps.asset_name, "ISL_LU_Interdependencies".aff_subm, "ISL_LU_Interdependencies".aff_netw_or_keys, existingInterdeps.gor_id, conversion_factor, modelrun_id_val
FROM
((SELECT gor_id, asset_name, interdep_ids FROM "EE_IO_GenerationAssetsByGOR" WHERE dn = 'Electricity' AND (NOT (interdep_ids = ''))) AS existingInterdeps
INNER JOIN "ISL_LU_Interdependencies" ON existingInterdeps.interdep_ids = "ISL_LU_Interdependencies".intdp_id)
WHERE "ISL_LU_Interdependencies".intdp_type = 'dir'  AND  "ISL_LU_Interdependencies".model_schema_id = model_schema_id_val

-- synergies  - entry in ISL_Interdependencies
-- START QUERY --
INSERT INTO "ISL_I_Interdependencies"(intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_name, aff_asset_type, aff_subm, aff_netw_or_keys, aff_reg1, aff_ass_name, conversion_factor, modelrun_id)
SELECT 'syn', 'Energy', 'Electricity', 'gen', existingInterdeps.gor_id, existingInterdeps.asset_name, 'gen', "ISL_LU_Interdependencies".aff_subm, "ISL_LU_Interdependencies".aff_netw_or_keys, existingInterdeps.gor_id, 
"ISL_LU_Interdependencies".aff_ass_name || existingInterdeps.asset_name, conversion_factor, modelrun_id_val FROM
((SELECT gor_id, asset_name, interdep_ids FROM "EE_IO_GenerationAssetsByGOR" WHERE dn = 'Electricity' AND (NOT (interdep_ids = ''))) AS existingInterdeps
INNER JOIN "ISL_LU_Interdependencies" ON existingInterdeps.interdep_ids = "ISL_LU_Interdependencies".intdp_id)
WHERE "ISL_LU_Interdependencies".intdp_type = 'syn' AND  "ISL_LU_Interdependencies".model_schema_id = model_schema_id_val

-- synergies - feedback assets
-- set capex and opex to 0
-- set capacity to 0!!!
-- START QUERY --
INSERT INTO "ISL_I_GenerationAssets"(dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, epi, comtype, submodel, cap_ceiling, region, asset_type, modelrun_id)
SELECT "ISL_LU_Interdependencies".aff_netw_or_keys, 0, instduration, maxlifetime, 0, rampspeed, 30, 2008,
"ISL_LU_Interdependencies".aff_ass_name || existingInterdeps.asset_name, 0, comtype, "ISL_LU_Interdependencies".aff_subm, cap_ceiling, existingInterdeps.gor_id, "ISL_LU_Interdependencies".aff_type, modelrun_id_val FROM
((SELECT gor_id, asset_name, interdep_ids, instduration, maxlifetime, maxcap, rampspeed, instdate, epi, comtype, cap_ceiling FROM "EE_IO_GenerationAssetsByGOR" WHERE dn = 'Electricity' AND (NOT (interdep_ids = ''))) AS existingInterdeps
INNER JOIN "ISL_LU_Interdependencies" ON existingInterdeps.interdep_ids = "ISL_LU_Interdependencies".intdp_id )
WHERE "ISL_LU_Interdependencies".intdp_type = 'syn'  AND  "ISL_LU_Interdependencies".model_schema_id = model_schema_id_val

