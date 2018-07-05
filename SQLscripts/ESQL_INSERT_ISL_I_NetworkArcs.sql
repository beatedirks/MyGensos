-- INSERT into ISL_I_NetworkArcs
-- inputs: list of valuenames and values


INSERT INTO "ISL_I_NetworkArcs" (cort,dn,origin,destination,maxcap,capex,instduration,maxlifetime,runcostperunit,instdate,epi,com_type, cap_ceiling, submodel, asset_name, modelrun_id)
SELECT cort_val,dn_val,origin_val,destination_val,maxcap_val,capex_val,instduration_val,maxlifetime_val,runcostperunit_val,instdate_val,
epi_val,com_type_val, cap_ceiling_val, submodel_val, asset_name_val, modelrun_id_val