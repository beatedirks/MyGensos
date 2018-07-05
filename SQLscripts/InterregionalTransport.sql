-- Loading the Transport Model for interregional transport

-- Keyservice
-- START QUERY --
INSERT INTO "ISL_I_KeyServices" (ks, kstype, supplynw, rc, epi, comfortfactorname, submodel, modelrun_id)
SELECT ks, kstype, supplynw, rc, epi, comfortfactor, submodel, modelrun_id_val
FROM "ISL_LU_KeyServices" WHERE submodel = 'Transport' AND model_schema_id = model_schema_id_val

-- Regions
-- START QUERY --
INSERT INTO "ISL_I_NetworkRegions" (regionname, submodel, modelrun_id) 
SELECT region_id, 'Transport', modelrun_id_val
FROM "ISL_LU_NetworkRegions" WHERE submodel = 'Transport' AND model_schema_id = model_schema_id_val

-- Interregional Transport Arcs -ROAD and RAIL
-- cost per trip with car/train estimated £50, plus electricity in case of electric options but this accounted for via interdependencies
-- emissions per trip with fuel car/train estimated to be 70/30kgs
-- emissions for electric options will be accounted for via interdependencies

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

-- START QUERY --
DO
$do$
BEGIN
IF (SELECT id FROM "ISL_LU_KeyServices" WHERE supplynw='RoadElectricCar' AND model_schema_id=model_schema_id_val) > 0 THEN
INSERT INTO "ISL_I_NetworkArcs" (cort, dn, maxcap, capex, instduration, maxlifetime, runcostperunit, instdate, epi, com_type, cap_ceiling, submodel, origin, destination, asset_name, modelrun_id)  
SELECT 'T', 'RoadElectricCar' , maxcap, capex, instduration, maxlifetime, 30, instdate, 0, 'roadelectriccar', cap_ceiling, submodel, gor_1, gor_2 , 'roadelectriccar' || '_' || gor_1 || '_' || gor_2 || '_' || instdate, modelrun_id_val
FROM "TR_LU_RoadCapacities" WHERE gor_1 <> gor_2 AND gor_1 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport') AND gor_2 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport');
END IF;
END 
$do$

-- START QUERY --
DO
$do$
BEGIN
IF (SELECT id FROM "ISL_LU_KeyServices" WHERE supplynw='RailElectric' AND model_schema_id=model_schema_id_val) > 0 THEN
INSERT INTO "ISL_I_NetworkArcs" (cort, dn, maxcap, capex, instduration, maxlifetime, runcostperunit, instdate, epi, com_type, cap_ceiling, submodel, origin, destination, asset_name, modelrun_id) 
SELECT 'T', 'RailElectric' , maxcap, capex, instduration, maxlifetime, 30, instdate, 0, 'electricrail', cap_ceiling, submodel, gor_1, gor_2 , 'electricrail' || '_' || gor_1 || '_' || gor_2 || '_' || instdate, modelrun_id_val
FROM "TR_LU_RailCapacities" WHERE gor_1 <> gor_2 AND gor_1 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport') AND gor_2 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport') AND diesel_or_electric = 'electric';
END IF;
END 
$do$


-- START QUERY --
DO
$do$
BEGIN
IF (SELECT id FROM "ISL_LU_KeyServices" WHERE supplynw='RailDiesel' AND model_schema_id=model_schema_id_val) > 0 THEN
INSERT INTO "ISL_I_NetworkArcs" (cort, dn, maxcap, capex, instduration, maxlifetime, runcostperunit, instdate, epi, com_type, cap_ceiling, submodel, origin, destination, asset_name, modelrun_id) 
SELECT 'T', 'RailDiesel' , maxcap, capex, instduration, maxlifetime, 100, instdate, 30, 'dieselrail', cap_ceiling, submodel, gor_1, gor_2 , 'dieselrail' || '_'|| gor_1 || '_' || gor_2 || '_'|| instdate, modelrun_id_val
FROM "TR_LU_RailCapacities" WHERE gor_1 <> gor_2 AND gor_1 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport') AND gor_2 IN (SELECT region_id FROM "ISL_LU_NetworkRegions" WHERE model_schema_id=model_schema_id_val AND submodel = 'Transport') AND diesel_or_electric = 'diesel';
END IF;
END 
$do$

-- Interdependencies
-- START QUERY --
-- direct interdependency: electricity demand of electric car journeys
-- conversion factor: 1 trip of ~100km needs 10kWhrs of electricity, i.e. 0.01 GWhrs -> conversion factor is 0.01
INSERT INTO "ISL_I_Interdependencies"(intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_reg2, caus_ass_name, aff_subm, aff_netw_or_keys, aff_reg1, conversion_factor, modelrun_id)
SELECT 'dir', 'Transport', 'RoadElectricCar', 'dist', origin, destination, 'roadelectriccar_' || origin || '_' || destination || '_' || instdate, 'Energy', 'electricity', origin, '0.01', modelrun_id_val
FROM "ISL_I_NetworkArcs"
WHERE dn = 'RoadElectricCar' and modelrun_id = modelrun_id_val

-- START QUERY --
-- direct interdependency: electricity demand of electric rail journeys
-- conversion factor: similar to electric cars?? -> 1 trip of ~100km needs 10kWhrs of electricity, i.e. 0.01 GWhrs -> conversion factor is 0.01
-- CHANGE BACK 0.1 to 0.01
INSERT INTO "ISL_I_Interdependencies"(intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_reg2, caus_ass_name, aff_subm, aff_netw_or_keys, aff_reg1, conversion_factor, modelrun_id)
SELECT 'dir', 'Transport', 'RailElectric', 'dist', origin, destination, 'electricrail_' || origin || '_' || destination || '_' || instdate, 'Energy', 'electricity', origin, '0.1', modelrun_id_val
FROM "ISL_I_NetworkArcs"
WHERE dn = 'RailElectric' and modelrun_id = modelrun_id_val

-- START QUERY --
-- add Road multiuse interdependency to ISL_I_Interdepdencies with values specified in GNE_LU_Interdependencies ID_ROAD:
-- for each Road arc add a multiuse interdependency relating to the respective local 'RoadFuelCar' arc, even for those themselves!
-- road capacities are given in trips in ISL_I_NetworkArcs - multiuse capacities should be given in PCUs - hence divide maxcap by 2
INSERT INTO "ISL_I_Interdependencies"(intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_reg2, caus_ass_name, aff_asset_type, aff_subm, aff_netw_or_keys, aff_reg1, aff_reg2, aff_ass_name, conversion_factor, max_cap, modelrun_id)
SELECT 'mult', 'Transport', 'RoadFuelCar', 'dist', origin, destination, 'roadfuelcar_' || origin || '_' || destination || '_' || instdate, 'dist', 'Transport', dn, origin, destination, asset_name,'0.5', maxcap*0.5, modelrun_id_val
FROM "ISL_I_NetworkArcs"
WHERE (dn = 'RoadFuelCar' OR dn = 'RoadElectricCar') and modelrun_id = modelrun_id_val


