-- orig caps given in 1Mcm/day: 1Mcm/day = 454 MW = 454*365*24/1000 GWhrs/year = 3978 GWhrs/year
-- gas prices is about £4 per mmbtu = £4 per 293KWhrs ->£ 13652 / GWhr

-- START QUERY --
DELETE FROM "EE_IO_GenerationAssetsByGOR"
WHERE dn = 'Gas'

-- START QUERY --
INSERT INTO "EE_IO_GenerationAssetsByGOR" (instdate, maxlifetime, maxcap, gor_id, asset_name, asset_type, dn, capex, instduration, rampspeed, cap_ceiling, submodel)
SELECT  inst_date, decom_date-inst_date+1 AS maxlifetime, cap*3978 AS tot_cap, "GOR", 1, 'LNG', 'Gas', 0, 0, 0, 0.9, 'Energy' FROM
(SELECT "GOR", MIN("Year") AS inst_date, MAX("Year") AS decom_date, AVG("LNGLimit") AS cap, model_schema_id FROM 
("EE_LU_GasSupplyByNode" INNER JOIN "EE_LU_RegionNode" ON "EE_LU_GasSupplyByNode"."Node" = "EE_LU_RegionNode"."NodeNum")
GROUP BY "GOR", "LNGLimit", model_schema_id) AS tab1 
WHERE model_schema_id = model_schema_id_val

-- START QUERY --
INSERT INTO "EE_IO_GenerationAssetsByGOR" (instdate, maxlifetime, maxcap, gor_id, asset_name, asset_type, dn, capex, instduration, rampspeed, cap_ceiling, submodel)
SELECT  inst_date, decom_date-inst_date+1 AS maxlifetime, cap*3978 AS tot_cap, "GOR", 1, 'Domestic','Gas', 0, 0, 0, 0.9, 'Energy' FROM
(SELECT "GOR", MIN("Year") AS inst_date, MAX("Year") AS decom_date, AVG("DomesticLimit") AS cap, model_schema_id FROM 
("EE_LU_GasSupplyByNode" INNER JOIN "EE_LU_RegionNode" ON "EE_LU_GasSupplyByNode"."Node" = "EE_LU_RegionNode"."NodeNum" )
GROUP BY "GOR", "DomesticLimit", model_schema_id) AS tab1 
WHERE model_schema_id = model_schema_id_val

-- START QUERY --
INSERT INTO "EE_IO_GenerationAssetsByGOR" (instdate, maxlifetime, maxcap, gor_id, asset_name, asset_type, dn, capex, instduration, rampspeed, cap_ceiling, submodel)
SELECT  inst_date, decom_date-inst_date+1 AS maxlifetime, cap*3978 AS tot_cap, "GOR", 1, 'Import1','Gas', 0, 0, 0, 0.9, 'Energy' FROM
(SELECT "GOR", MIN("Year") AS inst_date, MAX("Year") AS decom_date, AVG("ImportLimit1") AS cap, model_schema_id FROM 
("EE_LU_GasSupplyByNode" INNER JOIN "EE_LU_RegionNode" ON "EE_LU_GasSupplyByNode"."Node" = "EE_LU_RegionNode"."NodeNum" )
GROUP BY "GOR", "ImportLimit1", model_schema_id) AS tab1 
WHERE model_schema_id = model_schema_id_val

-- START QUERY --
INSERT INTO "EE_IO_GenerationAssetsByGOR" (instdate, maxlifetime, maxcap, gor_id, asset_name, asset_type, dn, capex, instduration, rampspeed, cap_ceiling, submodel)
SELECT  inst_date, decom_date-inst_date+1 AS maxlifetime, cap*3978 AS tot_cap, "GOR", 1, 'Import2','Gas', 0, 0, 0, 0.9, 'Energy' FROM
(SELECT "GOR", MIN("Year") AS inst_date, MAX("Year") AS decom_date, AVG("ImportLimit2") AS cap, model_schema_id FROM 
("EE_LU_GasSupplyByNode" INNER JOIN "EE_LU_RegionNode" ON "EE_LU_GasSupplyByNode"."Node" = "EE_LU_RegionNode"."NodeNum" )
GROUP BY "GOR", "ImportLimit2", model_schema_id) AS tab1 
WHERE model_schema_id = model_schema_id_val 

-- potential generation assets
-- START QUERY --
INSERT INTO "EE_IO_GenerationAssetsByGOR"(instdate, maxlifetime, maxcap, gor_id, asset_name, dn, instduration, rampspeed, cap_ceiling, submodel, asset_type, model_schema_id)
SELECT  100000000, maxlifetime, maxcap, "GOR", id+1555, 'Gas', instd, 0, 0.9, 'Energy', "Type", model_schema_id
FROM "EE_LU_OptionalGasGenerationAssetsByGOR" where model_schema_id = model_schema_id_val


-- START QUERY --
UPDATE "EE_IO_GenerationAssetsByGOR" SET 
runcostperunit = (SELECT runcost FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
epi = (SELECT epi FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
comtype = (SELECT com_type FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
interdep_ids = (SELECT interdependency_ids FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
capex = ("EE_IO_GenerationAssetsByGOR".maxcap * (SELECT capex_per_cap FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type))
WHERE dn = 'Gas'


-- TRANSMISSION ASSETS --
 
-- START QUERY --
DELETE FROM "EE_IO_TransmissionAssetsByGor"
WHERE network = 'Gas'

-- START QUERY --
-- add existing pipes from EE_LU_GasPipesByNode - that's what should be
INSERT INTO "EE_IO_TransmissionAssetsByGor" (network, origin_id, destination_id, submodel, maxcap, instduration, maxlifetime, instdate, capex, runcostperunit, epi, com_type, cap_ceiling, asset_name)
SELECT 'Gas', gor_1, gor_2, 'Energy', capacity, 0, 1000, 2000, 0, 10, 0, 'dummy', 0.9, 'Gas'  FROM
"EE_LU_ExistingGasTransmissionAssetsByGOR"








