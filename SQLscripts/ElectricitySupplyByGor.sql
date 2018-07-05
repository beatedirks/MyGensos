-- generation capacities are given in MW so they have to be converted into GWhrs/year: 365*24hrs/1000
-- runcost = £100000 per GWhr = £0.1 per kWhr
-- transmission capacities are given in MW, so they have to be converted into GWhrs/year: 365*24hrs/1000
-- runcost of transmission is estimated to be £0.01 per KWhr, i.e. £10000 per GWhr

-- GENERATION ASSETS --

-- START QUERY --
DELETE FROM "EE_IO_GenerationAssetsByGOR"
WHERE dn = 'Electricity'

-- START QUERY --
INSERT INTO "EE_IO_GenerationAssetsByGOR"(instdate, maxlifetime, maxcap, gor_id, asset_name, dn, capex, instduration, rampspeed, cap_ceiling, submodel, asset_type, model_schema_id)
SELECT  start, ("end"-start), 365*24*SUM("Capacity")/1000, "GOR", MAX(id), 'Electricity', 0, 0, 0, 0.9, 'Energy', "Type", model_schema_id
FROM "EE_LU_ExistingElectricityGenerationAssetsByBUS" where model_schema_id = model_schema_id_val
GROUP BY start, "end", "GOR", "Type",model_schema_id

-- potential assets
-- START QUERY --
INSERT INTO "EE_IO_GenerationAssetsByGOR"(instdate, maxlifetime, maxcap, gor_id, asset_name, dn, instduration, rampspeed, cap_ceiling, submodel, asset_type, model_schema_id)
SELECT  100000000, maxlifetime, maxcap, "GOR", id+555, 'Electricity', instd, 0, 0.9, 'Energy', "Type", model_schema_id
FROM "EE_LU_OptionalElectrictiyGenerationAssetsByGOR" where model_schema_id = model_schema_id_val

-- START QUERY --
UPDATE "EE_IO_GenerationAssetsByGOR" SET 
asset_type = (SELECT "Name" FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."GenType" = "EE_IO_GenerationAssetsByGOR".asset_type)
WHERE dn = 'Electricity'

-- START QUERY --
UPDATE "EE_IO_GenerationAssetsByGOR" SET 
runcostperunit = (SELECT runcost FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
epi = (SELECT epi FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
comtype = (SELECT com_type FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
interdep_ids = (SELECT interdependency_ids FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type),
capex = "EE_IO_GenerationAssetsByGOR".maxcap * (SELECT capex_per_cap FROM "EE_LU_AssetTypes" WHERE "EE_LU_AssetTypes"."Name" = "EE_IO_GenerationAssetsByGOR".asset_type)
WHERE dn = 'Electricity'


-- TRANSMISSION ASSETS --
 
-- START QUERY --
DELETE FROM "EE_IO_TransmissionAssetsByGor"
WHERE network = 'Electricity'

-- START QUERY --
INSERT INTO "EE_IO_TransmissionAssetsByGor" (network, origin_id, destination_id, submodel, maxcap, instduration, maxlifetime, instdate, capex, runcostperunit, epi, com_type, cap_ceiling, asset_name)
SELECT 'Electricity', gor_from, gor_id AS gor_to, 'Energy', 365*24*SUM(capacity)/1000, 0, 1000, 2000, 0, 10000, 0, 'dummy', 0.9, 'ElectricityArc'  FROM
(SELECT gor_id AS gor_from, "BusTo", capacity FROM
("EE_LU_ExistingElectricityTransmissionCapacitiesByBus" INNER JOIN "EE_LU_BusToGor" 
ON "EE_LU_ExistingElectricityTransmissionCapacitiesByBus"."BusFrom" = "EE_LU_BusToGor"."BusNum")) AS tabfrom
INNER JOIN "EE_LU_BusToGor" ON tabfrom."BusTo" = "EE_LU_BusToGor"."BusNum"
GROUP BY gor_from, gor_id


