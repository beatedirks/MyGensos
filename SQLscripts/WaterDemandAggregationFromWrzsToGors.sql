-- aggregate water demand from zones into GORs and save in  WS_LU_WaterDemandByGor table

-- START QUERY --
DELETE FROM "WS_LU_WaterDemandByGor"

-- START QUERY --
INSERT INTO "WS_LU_WaterDemandByGor"(gor_id, year, scenario_id, demand)
SELECT gor_id, year, modelrun_id, SUM(totaldemand)
FROM "WS_O_WRZones" INNER JOIN "WS_LU_WrzMappingOnGors" ON "WS_O_WRZones".wrz_id = "WS_LU_WrzMappingOnGors".wrz_id
GROUP BY gor_id, year, modelrun_id