INSERT INTO "WS_LU_WaterDemandByGor"(
            gor_id, year, modelrun_id, demand)
SELECT gor_id, year, modelrun_id, SUM(totaldemand) FROM (
"WS_LU_WrzMappingOnGors"
INNER JOIN
( SELECT * FROM "WS_O_WRZones" WHERE modelrun_id = 1802) AS intermed
ON intermed.wrz_id = "WS_LU_WrzMappingOnGors".wrz_id )
GROUP BY gor_id, year, modelrun_id