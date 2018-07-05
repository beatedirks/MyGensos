-- add keyservice to the modelrun input
-- inputs: list of values

INSERT INTO "ISL_I_KeyServices" (ks, kstype, supplynw, rc, epi, comfortfactorname, submodel, modelrun_id) 
SELECT ks_val, kstype_val, supplynw_val, rc_val, epi_val, comfortfactorname_val, submodel_val, modelrun_id_val
