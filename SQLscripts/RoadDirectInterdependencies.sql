-- direct interdependency: electricity demand of electric car journeys
-- conversion factor: 1 trip of ~100km needs 10kWhrs of electricity, i.e. 0.01 GWhrs -> conversion factor is 0.01

INSERT INTO "ISL_I_Interdependencies"(
            intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_reg2, caus_ass_name, aff_subm, aff_netw_or_keys, aff_reg1, conversion_factor, modelrun_id)
SELECT 'dir', 'Transport', 'RoadElectricCar', 'dist', origin, destination, CONCAT('roadelectriccar_', origin, '_', destination), 'Energy', 'electricity', origin, '0.01', modelrun_id_val
FROM "ISL_I_NetworkArcs"
WHERE dn = 'RoadElectricCar' and modelrun_id = modelrun_id_val
