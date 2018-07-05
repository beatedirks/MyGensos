-- add Road multiuse interdependency to ISL_I_Interdepdencies with values specified in GNE_LU_Interdependencies ID_ROAD:
-- for each Road arc add a multiuse interdependency relating to the respective local 'RoadFuelCar' arc, even for those themselves!
-- road capacities are given in trips in ISL_I_NetworkArcs - multiuse capacities should be given in PCUs - hence divide maxcap by 2
INSERT INTO "ISL_I_Interdependencies"(
            intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_reg2, caus_ass_name, aff_asset_type, aff_subm, aff_netw_or_keys, aff_reg1, aff_reg2, aff_ass_name, conversion_factor, max_cap, modelrun_id)
SELECT 'mult', 'Transport', 'RoadFuelCar', 'dist', origin, destination, CONCAT('roadfuelcar_', origin, '_', destination), 'dist', 'Transport', dn, origin, destination, asset_name,'0.5', maxcap*0.5, modelrun_id_val
FROM "ISL_I_NetworkArcs"
WHERE (dn = 'RoadFuelCar' OR dn = 'RoadElectricCar') and modelrun_id = modelrun_id_val
