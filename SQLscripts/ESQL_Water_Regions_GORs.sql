-- SQL SCRIPT TO SELECT THE GORs INVOLVED IN THE GIVEN MODELRUN:
-- inputs: submodel-modelrun_id as 'modelrun_id'

INSERT INTO "ISL_I_NetworkRegions" (regionname, submodel) 

SELECT gor_id, 'Water' FROM
-- retrieve all wrzs involved in the modelrun
((SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id =  ) AS wrzs
-- find the respective gors
INNER JOIN "WS_LU_WrzMappingOnGors"
ON wrzs.wrz_id = "WS_LU_WrzMappingOnGors".wrz_id)
GROUP BY gor_id
