-- add Electricity interdependencies to ISL_I_Interdepdencies with values specified in GNE_LU_Interdependencies

-- direct interdepedencies
-- START QUERY --
INSERT INTO "ISL_I_Interdependencies"(intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_name, aff_subm, aff_netw_or_keys, aff_reg1, conversion_factor, modelrun_id)
SELECT 'dir', 'Energy', 'Electricity', 'gen', existingInterdeps.gor_id, existingInterdeps.asset_name, "GNE_LU_Interdependencies".aff_subm, "GNE_LU_Interdependencies".aff_netw_or_keys, existingInterdeps.gor_id, conversion_factor, modelrun_id_val
FROM
((SELECT gor_id, asset_name, interdep_ids FROM "EE_IO_ExistingGenerationAssetsByGOR" WHERE dn = 'Electricity' AND (NOT (interdep_ids = ''))) AS existingInterdeps
INNER JOIN "GNE_LU_Interdependencies" ON existingInterdeps.interdep_ids = "GNE_LU_Interdependencies".intdp_id)
WHERE "GNE_LU_Interdependencies".intdp_type = 'dir'

-- synergies  - entry in ISL_Interdependencies
-- START QUERY --
INSERT INTO "ISL_I_Interdependencies"(intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_name, aff_asset_type, aff_subm, aff_netw_or_keys, aff_reg1, aff_ass_name, conversion_factor, modelrun_id)
SELECT 'syn', 'Energy', 'Electricity', 'gen', existingInterdeps.gor_id, existingInterdeps.asset_name, 'gen', "GNE_LU_Interdependencies".aff_subm, "GNE_LU_Interdependencies".aff_netw_or_keys, existingInterdeps.gor_id, 
CONCAT("GNE_LU_Interdependencies".aff_ass_name, existingInterdeps.asset_name), conversion_factor, modelrun_id_val FROM
((SELECT gor_id, asset_name, interdep_ids FROM "EE_IO_ExistingGenerationAssetsByGOR" WHERE dn = 'Electricity' AND (NOT (interdep_ids = ''))) AS existingInterdeps
INNER JOIN "GNE_LU_Interdependencies" ON existingInterdeps.interdep_ids = "GNE_LU_Interdependencies".intdp_id)
WHERE "GNE_LU_Interdependencies".intdp_type = 'syn'

-- synergies - feedback assets
-- set capex and opex to 0
-- set capacity to 0!!!
-- START QUERY --
INSERT INTO "ISL_I_GenerationAssets"(dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, epi, comtype, submodel, cap_ceiling, region, asset_type, modelrun_id)
SELECT "GNE_LU_Interdependencies".aff_netw_or_keys, 0, instduration, maxlifetime, 0, rampspeed, 0, 2008,
CONCAT("GNE_LU_Interdependencies".aff_ass_name, existingInterdeps.asset_name), epi, comtype, "GNE_LU_Interdependencies".aff_subm, cap_ceiling, existingInterdeps.gor_id, "GNE_LU_Interdependencies".aff_type, modelrun_id_val FROM
((SELECT gor_id, asset_name, interdep_ids, instduration, maxlifetime, maxcap, rampspeed, instdate, epi, comtype, cap_ceiling FROM "EE_IO_ExistingGenerationAssetsByGOR" WHERE dn = 'Electricity' AND (NOT (interdep_ids = ''))) AS existingInterdeps
INNER JOIN "GNE_LU_Interdependencies" ON existingInterdeps.interdep_ids = "GNE_LU_Interdependencies".intdp_id )
WHERE "GNE_LU_Interdependencies".intdp_type = 'syn'





