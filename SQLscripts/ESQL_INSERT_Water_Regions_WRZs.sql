-- SQL SCRIPT TO INSERT THE WRZs INVOLVED IN THE GIVEN MODELRUN into ISL_I_NetworkRegions:
-- inputs: submodel-modelrun_id as modelrun_id

INSERT INTO "ISL_I_NetworkRegions" (regionname, submodel) 

(SELECT wrz_id, 'Water' FROM "WS_I_WRZones_Run" WHERE modelrun_id =  )
