-- START QUERY --
DO
$do$
BEGIN
IF (SELECT id FROM "ISL_LU_KeyServices" WHERE supplynw='RoadFuelCar' AND model_schema_id=model_schema_id_val) > 0 THEN
	INSERT INTO "ISL_I_NetworkArcs" (cort, dn, maxcap, capex, instduration, maxlifetime, runcostperunit, instdate, epi, com_type, cap_ceiling, submodel, origin, destination, asset_name, modelrun_id)  
SELECT 'T', 'RoadFuelCar' , maxcap, capex, instduration, maxlifetime, 50, instdate, 70, 'roadfuelcar', cap_ceiling, submodel, gor_1, gor_2 , 'roadfuelcar' || '_' || gor_1 || '_' || gor_2 || '_' || instdate, modelrun_id_val
FROM "TR_LU_RoadCapacities" WHERE gor_1 <> gor_2 AND gor_1 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport') AND gor_2 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport');
END IF;
END 
$do$
