
INSERT INTO "ISL_I_GenerationAssets" 
(region, dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, epi, comtype, submodel, cap_ceiling, modelrun_id) 
SELECT
region_val, dn_val, capex_val, instduration_val, maxlifetime_val, maxcap_val, rampspeed_val, runcostperunit_val, 
instdate_val, asset_name_val, epi_val, comtype_val, submodel_val, cap_ceiling_val, modelrun_id_val